"""Resume a video pipeline: captions first, then audio download and Whisper only if needed."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from .path_utils import PROJECT_ROOT, project_path, report_path
    from .video_state import get, mark
except ImportError:
    from path_utils import PROJECT_ROOT, project_path, report_path
    from video_state import get, mark


def run_stage(script_name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", str(PROJECT_ROOT / "skills" / script_name), *args],
                         cwd=PROJECT_ROOT, check=True, text=True, encoding="utf-8", capture_output=True)


def _has_non_whitespace(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError):
        return False


def process(video_id: str, url: str, title: str = "", db_path: str | Path | None = None,
            mark_summarized: bool = False, channel_key: str | None = None) -> Path:
    state = get(video_id, db_path) or {"status": "pending", "subtitle_error": ""}
    docs = project_path("docs")
    existing_audio = next(docs.rglob(f"{video_id}.mp3"), None)
    existing_transcript = next(docs.rglob(f"{video_id}.txt"), None)
    if existing_audio is not None:
        target = existing_audio.parent
    elif existing_transcript is not None:
        target = existing_transcript.parent
    else:
        resolver_args = ["--create"]
        if channel_key:
            resolver_args.extend(["--channel-key", channel_key])
        info_result = run_stage("resolve_target_dir.py", url, *resolver_args)
        target_line = next(line for line in info_result.stdout.splitlines() if line.startswith("TARGET_DIR="))
        target = project_path(target_line.partition("=")[2])
        target.mkdir(parents=True, exist_ok=True)

    audio = target / f"{video_id}.mp3"
    transcript = target / f"{video_id}.txt"
    transcript_valid = _has_non_whitespace(transcript)
    if state["status"] == "complete" and transcript_valid:
        return target
    subtitle_error = state.get("subtitle_error", "")
    if state["status"] == "complete":
        mark(video_id, "pending", title=title, subtitle_error=subtitle_error, db_path=db_path)
        state["status"] = "pending"
    if mark_summarized:
        if not transcript_valid:
            raise FileNotFoundError(f"Cannot commit summary before a non-empty transcript exists: {transcript}")
        report = report_path(target)
        if not report.is_file():
            raise FileNotFoundError(f"Cannot commit summary before report exists: {report}")
        mark(video_id, "complete", title=title, db_path=db_path)
        return target

    if transcript_valid:
        mark(video_id, "transcript_ready", title=title,
             subtitle_error=subtitle_error, db_path=db_path)
        return target
    if transcript.exists() or state["status"] == "transcript_ready":
        mark(video_id, "pending", title=title, subtitle_error=subtitle_error, db_path=db_path)
        state["status"] = "pending"

    if state["status"] == "pending":
        try:
            run_stage("subtitle_to_text.py", url, "--output-dir", str(target), "--video-id", video_id)
            if not _has_non_whitespace(transcript):
                raise RuntimeError(f"Subtitle command did not create a non-empty transcript: {transcript}")
            mark(video_id, "transcript_ready", title=title, subtitle_error="", db_path=db_path)
            return target
        except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            subtitle_error = detail.strip() or repr(exc)
            mark(video_id, "pending", title=title, subtitle_error=subtitle_error, db_path=db_path)

    if not audio.is_file():
        try:
            run_stage("download_audio.py", url, "--output-dir", str(target))
        except (subprocess.CalledProcessError, OSError) as exc:
            mark(video_id, "pending", title=title, subtitle_error=subtitle_error, db_path=db_path)
            detail = getattr(exc, "stderr", None) or str(exc)
            raise RuntimeError(f"Audio download failed for {video_id}; subtitle attempt: {subtitle_error}\n{detail}") from exc
    if not audio.is_file():
        mark(video_id, "pending", title=title, subtitle_error=subtitle_error, db_path=db_path)
        raise FileNotFoundError(f"Audio download did not create the expected file: {audio}")
    mark(video_id, "audio", title=title, subtitle_error=subtitle_error, db_path=db_path)

    try:
        run_stage("transcribe.py", str(audio))
    except (subprocess.CalledProcessError, OSError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        raise RuntimeError(f"Transcription failed for {video_id}; subtitle attempt: {subtitle_error}\n{detail}") from exc
    if not _has_non_whitespace(transcript):
        empty_error = f"Transcription produced an empty or unreadable transcript: {transcript}"
        mark(video_id, "pending", title=title,
             subtitle_error=subtitle_error or empty_error, db_path=db_path)
        raise RuntimeError(f"{empty_error}; subtitle attempt: {subtitle_error or 'none recorded'}")
    mark(video_id, "transcript_ready", title=title, subtitle_error=subtitle_error, db_path=db_path)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--channel-key", choices=("cui", "meitou_news", "meitou_stock"),
                        help="由掃描器提供的穩定頻道鍵")
    parser.add_argument("--mark-summarized", action="store_true",
                        help="確認同目錄報告與文字稿存在後，提交 complete 狀態")
    args = parser.parse_args()
    try:
        target = process(args.video_id, args.url, args.title,
                         mark_summarized=args.mark_summarized, channel_key=args.channel_key)
        print(f"階段完成：{target}")
    except Exception as exc:
        print(f"處理失敗：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
