# /// script
# dependencies = [
#     "python-dotenv",
#     "yt-dlp",
# ]
# ///
"""
批次掃描頻道待處理影片並依美東日期分組 (List New Videos)

供 /process 工作流使用。掃描預設三個頻道；只略過 SQLite 狀態標記為 complete
的影片。下載日誌僅供舊歸檔工具使用，不代表處理完成。

用法：
  uv run skills/list_new_videos.py [--limit N] [--channel all|cui|meitou_news|meitou_stock] [--format human|json]

參數：
  --limit    每個頻道掃描最新的幾部影片（預設 8）
  --channel  指定掃描的頻道（預設 all，掃描全部三個頻道）
  --format   輸出格式：human（人類可讀，預設）或 json（機器可解析）

輸出（--format json）：
  {
    "generated_at": "<ISO 時間>",
    "total": <未下載影片總數>,
    "groups": [
      {
        "eastern_date": "YYYY-MM-DD",
        "videos": [
          {"id","title","channel_key","channel_name","url","eastern_datetime"}
        ]
      }
    ]
  }

注意：groups 依 eastern_date 由舊到新排序。若掃描時 Cookie 失效，會輸出 [COOKIE_ERROR] 並以結束代碼 2 結束。
"""
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from dotenv import load_dotenv

try:
    from .path_utils import PROJECT_ROOT, project_path
    from .video_state import is_complete
    from .log_download import extract_video_id
except ImportError:
    from path_utils import PROJECT_ROOT, project_path
    from video_state import is_complete
    from log_download import extract_video_id
EASTERN_TZ = "America/New_York"

# 頻道預設清單：key -> (顯示名稱, 清單 URL)
CHANNELS = {
    "cui": ("小翠時政財經", "https://www.youtube.com/@cui_news/streams"),
    "meitou_news": ("美投侃新聞", "https://www.youtube.com/@MeiTouNews/videos"),
    "meitou_stock": ("美投講美股", "https://www.youtube.com/@MeiTouJun/videos"),
}


def _reconfigure_utf8():
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding and stream.encoding.lower() != "utf-8":
            try:
                stream.reconfigure(encoding="utf-8")
            except AttributeError:
                pass


def _cookie_args():
    """Build yt-dlp cookie arguments from project-root .env settings."""
    browser = os.environ.get("COOKIES_BROWSER", "")
    if browser.lower() in ("none", "false", ""):
        browser = ""
    cookie_value = os.environ.get("COOKIES_PATH", "cookies.txt")
    cookie_path = project_path(cookie_value) if cookie_value and cookie_value.lower() not in ("none", "false") else None
    if cookie_path and cookie_path.is_file():
        return ["--cookies", str(cookie_path)]
    if browser:
        return ["--cookies-from-browser", browser]
    return []


class CookieError(Exception):
    pass


def _run_yt_dlp(extra_args):
    cmd = [sys.executable, "-m", "yt_dlp"] + extra_args
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr_lower = (e.stderr or "").lower()
        if any(k in stderr_lower for k in ["sign in", "bot", "cookie", "member", "private"]):
            raise CookieError(e.stderr)
        raise


def to_epoch(timestamp_raw, release_raw):
    for raw in (timestamp_raw, release_raw):
        if raw and raw not in ("NA", "None", ""):
            try:
                return int(float(raw))
            except ValueError:
                continue
    return None


def epoch_to_eastern(epoch):
    dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)
    if ZoneInfo is not None:
        return dt_utc.astimezone(ZoneInfo(EASTERN_TZ))
    return dt_utc  # 無 zoneinfo 時退回 UTC


def fetch_channel_entries(url, limit, cookie_args):
    """以 flat-playlist 取得頻道最新 limit 部影片的原始欄位。"""
    print_fmt = "%(id)s|%(title)s|%(webpage_url)s|%(timestamp)s|%(release_timestamp)s|%(upload_date)s"
    out = _run_yt_dlp([
        "--flat-playlist",
        "--print", print_fmt,
        "--playlist-end", str(limit),
        *cookie_args,
        url,
    ])
    entries = []
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 3:
            continue
        entries.append({
            "id": parts[0],
            "title": parts[1],
            "url": parts[2],
            "timestamp": parts[3] if len(parts) > 3 else "",
            "release_timestamp": parts[4] if len(parts) > 4 else "",
            "upload_date": parts[5] if len(parts) > 5 else "",
        })
    return entries


def fetch_single_time(url, cookie_args):
    """對單一影片取得精確時間（flat-playlist 缺 timestamp 時的後備）。回傳 (epoch, upload_date)。"""
    try:
        out = _run_yt_dlp([
            "--no-download",
            "--print", "%(timestamp)s|%(release_timestamp)s|%(upload_date)s",
            *cookie_args,
            url,
        ])
    except (subprocess.CalledProcessError, CookieError):
        return None, ""
    line = out.splitlines()[0] if out else ""
    parts = line.split("|")
    ts = parts[0] if len(parts) > 0 else ""
    rel = parts[1] if len(parts) > 1 else ""
    upload_date = parts[2] if len(parts) > 2 else ""
    return to_epoch(ts, rel), upload_date


def collect_new_videos(channel_keys, limit, cookie_args):
    """Scan channels and omit only videos whose full processing completed."""
    videos = []
    for key in channel_keys:
        channel_name, url = CHANNELS[key]
        entries = fetch_channel_entries(url, limit, cookie_args)
        for entry in entries:
            video_id = extract_video_id(entry["url"]) or entry["id"]
            if is_complete(video_id):
                continue

            epoch = to_epoch(entry["timestamp"], entry["release_timestamp"])
            upload_date = entry["upload_date"]
            # flat-playlist 常缺 timestamp，改對單一影片補抓精確時間
            if epoch is None:
                epoch, single_upload_date = fetch_single_time(entry["url"], cookie_args)
                upload_date = upload_date or single_upload_date

            if epoch is not None:
                dt_et = epoch_to_eastern(epoch)
                eastern_date = dt_et.strftime("%Y-%m-%d")
                eastern_datetime = dt_et.strftime("%Y-%m-%d %H:%M ET")
            elif upload_date and len(upload_date) == 8 and upload_date not in ("NA", "None"):
                eastern_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                eastern_datetime = f"{eastern_date} (僅日期)"
            else:
                eastern_date = "未知日期"
                eastern_datetime = "未知"

            videos.append({
                "id": video_id,
                "title": entry["title"],
                "channel_key": key,
                "channel_name": channel_name,
                "url": entry["url"],
                "eastern_date": eastern_date,
                "eastern_datetime": eastern_datetime,
            })
    return videos


def group_by_date(videos):
    groups = {}
    for v in videos:
        groups.setdefault(v["eastern_date"], []).append(v)
    # 依日期由舊到新排序；「未知日期」排最後
    def sort_key(d):
        return (d == "未知日期", d)
    result = []
    for date in sorted(groups.keys(), key=sort_key):
        vids = groups[date]
        vids.sort(key=lambda x: x["eastern_datetime"])
        result.append({
            "eastern_date": date,
            "videos": [
                {k: v[k] for k in ("id", "title", "channel_key", "channel_name", "url", "eastern_datetime")}
                for v in vids
            ],
        })
    return result


def print_human(groups, total):
    if total == 0:
        print("✅ 三個頻道皆無未下載的新影片。")
        return
    print(f"🔎 共發現 {total} 部未下載影片，依美東日期分為 {len(groups)} 組（由舊到新）：\n")
    for i, g in enumerate(groups, 1):
        print(f"── 第 {i} 組｜美東日期 {g['eastern_date']}（{len(g['videos'])} 部）")
        for v in g["videos"]:
            print(f"    • [{v['channel_name']}] {v['title']}")
            print(f"      時間：{v['eastern_datetime']}｜URL：{v['url']}")
        print()


def main():
    _reconfigure_utf8()
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="批次掃描頻道待處理影片並依美東日期分組")
    parser.add_argument("--limit", type=int, default=8, help="每個頻道掃描最新的幾部影片（預設 8）")
    parser.add_argument(
        "--channel",
        choices=["all", "cui", "meitou_news", "meitou_stock"],
        default="all",
        help="要掃描的頻道（預設 all）",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="輸出格式（預設 human）",
    )
    args = parser.parse_args()

    channel_keys = list(CHANNELS.keys()) if args.channel == "all" else [args.channel]
    cookie_args = _cookie_args()

    try:
        videos = collect_new_videos(channel_keys, args.limit, cookie_args)
    except CookieError as e:
        print(
            f"\n[COOKIE_ERROR] YouTube 拒絕存取。Cookie 可能無效、過期或未提供。\n詳細錯誤: {e}",
            file=sys.stderr,
        )
        sys.exit(2)

    groups = group_by_date(videos)
    total = len(videos)

    if args.format == "json":
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "groups": groups,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(groups, total)


if __name__ == "__main__":
    main()
