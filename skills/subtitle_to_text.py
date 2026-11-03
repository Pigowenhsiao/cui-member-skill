# /// script
# dependencies = [
#     "python-dotenv",
#     "yt-dlp",
# ]
# ///

"""Download preferred YouTube captions or convert a local WebVTT file to UTF-8 text."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

try:
    from .path_utils import PROJECT_ROOT, project_path
except ImportError:
    from path_utils import PROJECT_ROOT, project_path

LANGUAGE_PREFERENCE = "manual tracks before automatic; within each, Traditional Chinese, other Chinese, then English"
_TAGS = re.compile(r"<[^>]*>")
_TIMECODE = re.compile(r"^(?:\d{2}:)?\d{2}:\d{2}[.,]\d{3}\s+-->\s+(?:\d{2}:)?\d{2}:\d{2}[.,]\d{3}(?:\s+.*)?$")


def vtt_to_text(content: str) -> str:
    lines: list[str] = []
    previous = None
    for raw in content.replace("\ufeff", "").splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "REGION")) or _TIMECODE.match(line) or line.isdigit():
            continue
        text = html.unescape(_TAGS.sub("", re.sub(r"<(?:\d{2}:)?\d{2}:\d{2}[.,]\d{3}>", "", line))).strip()
        if text and text != previous:
            lines.append(text)
            previous = text
    return "\n".join(lines).strip()


def _cookies() -> list[str]:
    load_dotenv(PROJECT_ROOT / ".env")
    browser = os.environ.get("COOKIES_BROWSER", "")
    if browser.lower() in ("none", "false", ""):
        browser = ""
    cookie_value = os.environ.get("COOKIES_PATH", "cookies.txt")
    cookie_path = project_path(cookie_value) if cookie_value and cookie_value.lower() not in ("none", "false") else None
    if cookie_path and cookie_path.is_file():
        return ["--cookies", str(cookie_path)]
    return ["--cookies-from-browser", browser] if browser else []


def _yt_dlp(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "yt_dlp", *args], cwd=PROJECT_ROOT,
                          check=True, text=True, encoding="utf-8", capture_output=True)


def _language_rank(language: str) -> tuple[int, str]:
    normalized = language.casefold().replace("_", "-")
    if normalized.startswith("zh-hant") or normalized.startswith(("zh-tw", "zh-hk", "zh-mo")):
        return 0, normalized
    if normalized.startswith("zh"):
        return 1, normalized
    if normalized.startswith("en"):
        return 2, normalized
    return 3, normalized


def _select_tracks(metadata: dict) -> list[tuple[str, bool]]:
    tracks = []
    for available, is_automatic in ((metadata.get("subtitles") or {}, False),
                                    (metadata.get("automatic_captions") or {}, True)):
        tracks.extend((language, is_automatic)
                      for language in sorted(available, key=_language_rank)
                      if _language_rank(language)[0] < 3)
    return tracks


def _select_track(metadata: dict) -> tuple[str, bool] | None:
    tracks = _select_tracks(metadata)
    return tracks[0] if tracks else None


def download_subtitle(url: str, output_dir: Path, video_id: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cookies = _cookies()
    metadata = json.loads(_yt_dlp(["--skip-download", "--dump-single-json", "--no-playlist", *cookies, url]).stdout)
    video_id = video_id or metadata.get("id", "")
    if not video_id:
        raise RuntimeError("yt-dlp metadata did not include a video ID.")
    tracks = _select_tracks(metadata)
    if not tracks:
        raise RuntimeError(f"No supported caption tracks; preference: {LANGUAGE_PREFERENCE}.")

    failures = []
    for language, automatic in tracks:
        args = ["--skip-download", "--sub-format", "vtt", "--sub-langs", language]
        args.append("--write-auto-subs" if automatic else "--write-subs")
        args.extend(cookies)
        try:
            with tempfile.TemporaryDirectory(prefix=".captions-", dir=output_dir) as temporary:
                args.extend(["-o", str(Path(temporary) / f"{video_id}.%(ext)s"), url])
                _yt_dlp(args)
                candidates = sorted(Path(temporary).glob(f"{video_id}.{language}*.vtt"))
                if not candidates:
                    raise RuntimeError(f"No VTT file created for track {language}")
                transcript = vtt_to_text(candidates[0].read_text(encoding="utf-8"))
            if not transcript:
                raise RuntimeError(f"Track {language} contained no usable transcript text")
            output = output_dir / f"{video_id}.txt"
            output.write_text(transcript + "\n", encoding="utf-8")
            return output
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            failures.append(f"{language} ({'automatic' if automatic else 'manual'}): {detail.strip()}")
    raise RuntimeError("All available caption tracks failed: " + " | ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="YouTube URL or local .vtt file")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--video-id", default="")
    args = parser.parse_args()
    source = project_path(args.source)
    try:
        if source.is_file() and source.suffix.lower() == ".vtt":
            text = vtt_to_text(source.read_text(encoding="utf-8"))
            if not text:
                raise RuntimeError(f"No usable caption text in {source}")
            target = source.with_suffix(".txt")
            target.write_text(text + "\n", encoding="utf-8")
        else:
            target = download_subtitle(args.source, project_path(args.output_dir), args.video_id)
        print(f"字幕文字稿已保存：{target}")
    except Exception as exc:
        print(f"字幕下載或轉換失敗：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
