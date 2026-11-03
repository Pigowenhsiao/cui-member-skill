# /// script
# dependencies = []
# ///
"""
下載紀錄管理工具 (Download Log Manager)

用於操作與管理 logs/download.log 的通用腳本。
供其他技能 (scan_*, download_audio.py) 呼叫使用。

使用方法:
  uv run skills/log_download.py check <URL 或 影片ID>
  uv run skills/log_download.py add <URL>

子命令:
  check  - 檢查指定的 URL/影片ID 是否已存在於下載紀錄中
           若存在: 結束代碼 0，輸出 "[FOUND]"
           若不存在: 結束代碼 1，輸出 "[NOT_FOUND]"

  add    - 將指定的 URL 寫入下載紀錄中
           輸出 "[LOGGED]" 並以結束代碼 0 結束
"""
import os
import sys
import re
import argparse
import datetime

try:
    from .path_utils import PROJECT_ROOT
except ImportError:
    from path_utils import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "download.log"


def extract_video_id(url_or_id: str) -> str:
    """從 YouTube URL 中提取影片 ID。若傳入的已是 ID 則直接返回。"""
    # 模式: watch?v=ID, /live/ID, youtu.be/ID, /shorts/ID, /embed/ID
    patterns = [
        r"[?&]v=([a-zA-Z0-9_-]{11})",
        r"/live/([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"/shorts/([a-zA-Z0-9_-]{11})",
        r"/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    # 若未匹配到 URL 模式，則視為 ID 本身
    stripped = url_or_id.strip()
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", stripped):
        return stripped

    return stripped


def check_log(identifier: str) -> bool:
    """檢查日誌檔案中是否存在指定的影片 ID。"""
    video_id = extract_video_id(identifier)

    if not os.path.exists(LOG_FILE):
        return False

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if video_id in line:
                return True
    return False


def add_log(url: str) -> None:
    """將下載紀錄附加至日誌檔案中。"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Downloaded: {url}\n")


def main():
    parser = argparse.ArgumentParser(
        description="下載紀錄管理工具 (Download Log Manager)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check 子命令
    check_parser = subparsers.add_parser(
        "check", help="檢查 URL/影片ID 是否已存在於紀錄中"
    )
    check_parser.add_argument(
        "identifier", help="YouTube URL 或 影片 ID"
    )

    # add 子命令
    add_parser = subparsers.add_parser(
        "add", help="將下載紀錄寫入日誌"
    )
    add_parser.add_argument("url", help="已下載的 YouTube URL")

    args = parser.parse_args()

    if args.command == "check":
        video_id = extract_video_id(args.identifier)
        found = check_log(args.identifier)
        if found:
            print(f"[FOUND] 影片 ID '{video_id}' 已存在於 {LOG_FILE} 中。")
            sys.exit(0)
        else:
            print(f"[NOT_FOUND] 影片 ID '{video_id}' 不存在於 {LOG_FILE} 中。")
            sys.exit(1)

    elif args.command == "add":
        add_log(args.url)
        video_id = extract_video_id(args.url)
        print(f"[LOGGED] 已記錄: {args.url} (影片 ID: {video_id})")


if __name__ == "__main__":
    main()
