# /// script
# dependencies = [
#     "python-dotenv",
#     "yt-dlp",
# ]
# ///
import os
import sys
import argparse
import subprocess
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9 後備
    ZoneInfo = None

from dotenv import load_dotenv

EASTERN_TZ = "America/New_York"


def to_eastern_str(timestamp_raw: str, release_raw: str, upload_date_raw: str) -> str:
    """將 yt-dlp 的時間欄位轉換為美東時間字串 (YYYY-MM-DD HH:MM ET)。

    優先使用 Unix epoch（timestamp / release_timestamp），
    若皆缺失則退回 upload_date（僅日期，格式 YYYYMMDD）。
    無法取得時回傳「未知」。
    """
    epoch = None
    for raw in (timestamp_raw, release_raw):
        if raw and raw not in ("NA", "None", ""):
            try:
                epoch = int(float(raw))
                break
            except ValueError:
                continue

    if epoch is not None and ZoneInfo is not None:
        dt_et = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(ZoneInfo(EASTERN_TZ))
        return dt_et.strftime("%Y-%m-%d %H:%M ET")

    if epoch is not None:  # 無 zoneinfo 時退回 UTC 標示
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if upload_date_raw and upload_date_raw not in ("NA", "None", "") and len(upload_date_raw) == 8:
        return f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]} (僅日期)"

    return "未知"


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(description="取得指定 YouTube 頻道的最新影片標題與 URL")
    parser.add_argument("url", help="頻道的 videos 或 streams URL", default="https://www.youtube.com/@cui_news/streams", nargs="?")
    parser.add_argument("--limit", type=int, default=1, help="取得最新的幾部影片（預設 1）")
    parser.add_argument(
        "--with-time",
        action="store_true",
        help="在每行輸出附加影片的美東上傳/開播時間（格式：<標題>|<URL>|<美東時間>）",
    )
    args = parser.parse_args()

    # 載入 .env
    load_dotenv()

    browser = os.environ.get("COOKIES_BROWSER", "")
    if browser and browser.lower() in ("none", "false", ""):
        browser = None

    cookies_file = os.environ.get("COOKIES_PATH", "./cookies.txt")

    # yt-dlp 命令：取得最新數部影片的標題、URL 與時間欄位
    # 使用 flat-playlist 以加速；時間欄位在部分頻道下可能為 NA，屆時以 --with-time 的後備邏輯處理。
    print_fmt = "%(title)s|%(webpage_url)s|%(timestamp)s|%(release_timestamp)s|%(upload_date)s"
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--flat-playlist",
        "--print", print_fmt,
        "--playlist-end", str(args.limit),
        args.url
    ]

    if os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    elif browser:
        cmd.extend(["--cookies-from-browser", browser])

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if not output:
            print("無法取得最新的影片資訊。")
            sys.exit(1)

        for line in output.splitlines():
            parts = line.split("|")
            # 至少要有 標題 與 URL
            if len(parts) < 2:
                continue
            title = parts[0]
            url = parts[1]
            if args.with_time:
                timestamp_raw = parts[2] if len(parts) > 2 else ""
                release_raw = parts[3] if len(parts) > 3 else ""
                upload_date_raw = parts[4] if len(parts) > 4 else ""
                eastern = to_eastern_str(timestamp_raw, release_raw, upload_date_raw)
                print(f"{title}|{url}|{eastern}")
            else:
                # 維持向後相容的輸出格式：<標題>|<URL>
                print(f"{title}|{url}")
    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower() if e.stderr else ""
        if any(keyword in stderr_lower for keyword in ["sign in", "bot", "cookie", "member", "private"]):
            print(f"\n[COOKIE_ERROR] YouTube 拒絕存取。Cookie 可能無效、過期或未提供。\n詳細錯誤: {e.stderr}", file=sys.stderr)
        else:
            print(f"查詢失敗: {e.stderr}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
