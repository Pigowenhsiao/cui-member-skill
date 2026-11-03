# /// script
# dependencies = []
# ///
"""
讀取 yt-dlp 產生的 .info.json 中繼資料檔案，
並以結構化格式輸出影片的關鍵資訊，供 AI Agent 在 /organize 等步驟中使用。

用法：
  uv run skills/read_metadata.py <info.json 路徑> [<info.json 路徑> ...]

輸出格式（每個檔案一行）：
  id|title|channel|upload_date|url|duration_seconds

範例：
  uv run skills/read_metadata.py eG4NrYSvJ9o.info.json
  uv run skills/read_metadata.py docs/小翠時政財經/每日要聞/20260805/*.info.json
"""
import json
import sys
import argparse
import os


def read_metadata(filepath: str) -> dict:
    """讀取 .info.json 並回傳關鍵欄位字典。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "id": data.get("id", ""),
        "title": data.get("title", ""),
        "channel": data.get("channel", data.get("uploader", "")),
        "upload_date": data.get("upload_date", ""),
        "url": data.get("webpage_url", data.get("original_url", "")),
        "duration": data.get("duration", 0),
        "live_status": data.get("live_status", ""),
        "categories": ", ".join(data.get("categories", [])),
    }


def format_line(meta: dict) -> str:
    """將 metadata 字典格式化為 pipe-delimited 一行輸出。"""
    return "|".join([
        meta["id"],
        meta["title"],
        meta["channel"],
        meta["upload_date"],
        meta["url"],
        str(meta["duration"]),
    ])


def format_human(meta: dict, filepath: str) -> str:
    """將 metadata 字典格式化為人類可讀的多行輸出。"""
    duration_s = int(meta["duration"]) if meta["duration"] else 0
    minutes, seconds = divmod(duration_s, 60)
    hours, minutes = divmod(minutes, 60)
    duration_str = f"{hours}h{minutes:02d}m{seconds:02d}s" if hours else f"{minutes}m{seconds:02d}s"

    lines = [
        f"📄 檔案：{filepath}",
        f"  影片 ID    ：{meta['id']}",
        f"  標題       ：{meta['title']}",
        f"  頻道       ：{meta['channel']}",
        f"  上傳日期   ：{meta['upload_date']}",
        f"  影片 URL   ：{meta['url']}",
        f"  時長       ：{duration_str} ({duration_s}s)",
    ]
    if meta["live_status"]:
        lines.append(f"  直播狀態   ：{meta['live_status']}")
    if meta["categories"]:
        lines.append(f"  分類       ：{meta['categories']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="讀取 yt-dlp 的 .info.json 中繼資料，輸出影片關鍵資訊"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help=".info.json 檔案路徑（可指定多個）",
    )
    parser.add_argument(
        "--format",
        choices=["human", "pipe", "json"],
        default="human",
        help="輸出格式：human（人類可讀，預設）、pipe（管道分隔）、json（JSON 物件）",
    )
    args = parser.parse_args()

    results = []
    for filepath in args.files:
        if not os.path.exists(filepath):
            print(f"⚠️  檔案不存在：{filepath}", file=sys.stderr)
            continue

        try:
            meta = read_metadata(filepath)
            results.append((filepath, meta))
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"⚠️  讀取失敗 ({filepath})：{e}", file=sys.stderr)
            continue

    if not results:
        print("未找到任何有效的 .info.json 檔案。", file=sys.stderr)
        sys.exit(1)

    if args.format == "pipe":
        # 標頭
        print("id|title|channel|upload_date|url|duration")
        for _, meta in results:
            print(format_line(meta))
    elif args.format == "json":
        output = [meta for _, meta in results]
        if len(output) == 1:
            print(json.dumps(output[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(output, ensure_ascii=False, indent=2))
    else:  # human
        for filepath, meta in results:
            print(format_human(meta, filepath))
            print()


if __name__ == "__main__":
    main()
