# /// script
# dependencies = [
#     "python-dotenv",
# ]
# ///
import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="取得指定 YouTube 頻道的最新影片標題與 URL")
    parser.add_argument("url", help="頻道的 videos 或 streams URL", default="https://www.youtube.com/@cui_news/streams", nargs="?")
    args = parser.parse_args()

    # 載入 .env
    load_dotenv()

    browser = os.environ.get("COOKIES_BROWSER", "chrome")
    if browser and browser.lower() in ("none", "false", ""):
        browser = None

    cookies_file = os.environ.get("COOKIES_PATH", "./cookies.txt")

    # yt-dlp 命令：取得最新一部影片的標題與URL
    cmd = [
        "yt-dlp",
        "--print", "%(title)s|%(webpage_url)s",
        "--playlist-end", "1",
        args.url
    ]
    
    if os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    elif browser:
        cmd.extend(["--cookies-from-browser", browser])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            print(output)
        else:
            print("無法取得最新的影片資訊。")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"查詢失敗: {e.stderr}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
