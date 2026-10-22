#!/usr/bin/env python3
"""從 YouTube 自動字幕（VTT）產生純文字稿。

用途：當影片有自動生成字幕時，可取代 Whisper 轉譯，速度快且字詞正確率較高。

用法：
    # 由 YouTube URL 直接下載字幕並轉換
    uv run skills/subtitle_to_text.py "https://youtu.be/VIDEO_ID"

    # 由本地 .vtt 檔轉換
    uv run skills/subtitle_to_text.py path/to/VIDEO_ID.zh-Hant.vtt

選項：
    --lang zh-Hant     字幕語言代碼（預設 zh-Hant）
    --out PATH         輸出 .txt 路徑（預設與字幕同目錄、同名 .txt）
    --keep-vtt         保留下載的 .vtt 檔
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

# 去除 VTT 行內標記：<c>、<00:00:01.234>、<i>、</i> 等
_TAG_RE = re.compile(r"<[^>]+>")
# 時間戳行：00:00:00.100 --> 00:00:02.893 align:start position:0%
_CUE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->")
_NBSP = " "
_HEADER_PREFIXES = ("WEBVTT", "Kind:", "Language:")


def clean_line(line: str) -> str:
    """去除行內標記與多餘空白，保留原始文字。"""
    line = _TAG_RE.sub("", line)
    line = line.replace(_NBSP, " ")
    return line.strip()


def parse_vtt(vtt_text: str) -> list[str]:
    """解析 VTT，回傳每個 cue 的「最後一行非空文字」。

    YouTube 自動字幕為滾動式結構：每個 cue 的第一行是上一段已結算的文字，
    最後一行才是新出現的內容。取最後一行再對累積文字做去重即可還原完整稿。
    """
    cues: list[str] = []
    in_cue = False
    lines: list[str] = []

    def flush() -> None:
        if not lines:
            return
        candidates = [clean_line(line) for line in lines]
        candidates = [c for c in candidates if c]
        if candidates:
            cues.append(candidates[-1])
        _ = lines.clear()

    for raw in vtt_text.splitlines():
        if raw.startswith(_HEADER_PREFIXES):
            continue
        if raw.strip() == "":
            flush()
            in_cue = False
            continue
        if _CUE_RE.match(raw.strip()):
            flush()
            in_cue = True
            continue
        if in_cue:
            lines.append(raw)
    flush()
    return cues


def cues_to_text(cues: list[str]) -> str:
    """將 cue 序列還原為連續文字稿，去除重複行。"""
    out: list[str] = []
    acc = ""
    for cue in cues:
        if not cue:
            continue
        if acc and acc.endswith(cue):
            continue
        if acc and cue.startswith(acc):
            cue = cue[len(acc):]
        acc += cue
        out.append(cue)
    return "".join(out)


def download_subtitle(url: str, lang: str, out_dir: Path,
                      cookies: str | None = None) -> Path:
    """用 yt-dlp 下載自動生成的字幕，回傳 .vtt 路徑。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-langs", lang,
        "--sub-format", "vtt",
        "--skip-download",
        "--no-playlist",
        "-o", str(out_dir / "%(id)s.%(ext)s"),
    ]
    if cookies and Path(cookies).exists():
        cmd += ["--cookies", cookies]
    cmd.append(url)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        _ = sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(f"yt-dlp 下載字幕失敗 (exit {proc.returncode})")

    candidates = sorted(out_dir.glob(f"*.{lang}.vtt"))
    if not candidates:
        raise SystemExit(f"找不到 {lang} 字幕檔：{out_dir}")
    return candidates[0]


def resolve_output_path(vtt_path: Path, lang: str, out: str | None) -> Path:
    """決定輸出 .txt 路徑。"""
    if out:
        return Path(out)
    return vtt_path.with_name(vtt_path.name.replace(f".{lang}.vtt", ".txt"))


def main() -> None:
    ap = argparse.ArgumentParser(description="從 YouTube 自動字幕產生純文字稿")
    _ = ap.add_argument("source", help="YouTube URL 或本地 .vtt 檔")
    _ = ap.add_argument("--lang", default="zh-Hant", help="字幕語言代碼")
    _ = ap.add_argument("--out", default=None, help="輸出 .txt 路徑")
    _ = ap.add_argument("--out-dir", default=".", help="URL 模式下字幕的下載目錄")
    _ = ap.add_argument("--cookies", default=None, help="yt-dlp cookies 檔路徑")
    _ = ap.add_argument("--keep-vtt", action="store_true", help="保留下載的 .vtt 檔")
    args = ap.parse_args()

    source = cast(str, args.source)
    lang = cast(str, args.lang)
    out_arg = cast(str | None, args.out)
    out_dir_arg = cast(str, args.out_dir)
    cookies_arg = cast(str | None, args.cookies)
    keep_vtt = cast(bool, args.keep_vtt)

    is_url = "://" in source
    src = Path(source)
    if is_url:
        vtt_path = download_subtitle(
            source, lang, Path(out_dir_arg), cookies_arg
        )
    elif src.suffix.lower() == ".vtt" and src.exists():
        vtt_path = src
    else:
        raise SystemExit(f"無法處理的來源：{source}（需為 YouTube URL 或存在的 .vtt 檔）")

    text = cues_to_text(parse_vtt(vtt_path.read_text(encoding="utf-8")))

    out_path = resolve_output_path(vtt_path, lang, out_arg)
    _ = out_path.write_text(text, encoding="utf-8")

    if is_url and not keep_vtt:
        _ = vtt_path.unlink(missing_ok=True)

    print(f"輸出：{out_path}")
    print(f"字數：{len(text)} 字")


if __name__ == "__main__":
    main()
