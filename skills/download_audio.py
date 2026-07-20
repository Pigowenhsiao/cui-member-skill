# /// script
# dependencies = [
#     "python-dotenv",
# ]
# ///
import os
import sys
import subprocess
import argparse
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="下載 YouTube 音訊並保留標題等中繼資料 (Metadata)")
    parser.add_argument("url", help="YouTube 影片或播放清單 URL")
    parser.add_argument("--cookies", help="Cookies 檔案路徑", default=None)
    parser.add_argument("--browser", help="從指定的瀏覽器直接讀取 Cookies (例如 firefox, chrome, safari, edge)", default=None)
    args = parser.parse_args()

    # 載入 .env
    load_dotenv()

    browser = args.browser
    if browser is None:
        browser = os.environ.get("COOKIES_BROWSER", "chrome")
    if browser and browser.lower() in ("none", "false", ""):
        browser = None

    cookies_file = args.cookies
    if not cookies_file:
        cookies_file = os.environ.get("COOKIES_PATH", "./cookies.txt")

    print(f"正在從 {args.url} 下載音訊...")
    if os.path.exists(cookies_file):
        print(f"使用 Cookies 檔案: {cookies_file}")
    elif browser:
        print(f"自動讀取瀏覽器 Cookies: {browser}")
    else:
        print("未找到或未使用 Cookies 檔案。")

    # yt-dlp 命令：
    # -x, --audio-format mp3: 提取音訊並轉為 mp3
    # --write-info-json: 將影片標題、頻道等中繼資料寫入 JSON，方便 AI Agent 後續分析
    # -o: 指定輸出檔名格式
    cmd = [
        "yt-dlp",
        "--windows-filenames",
        "-x",
        "--audio-format",
        "mp3",
        "--write-info-json",
        "-o",
        "%(id)s.%(ext)s"
    ]
    
    if cookies_file and os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    elif browser:
        cmd.extend(["--cookies-from-browser", browser])
    
    cmd.append(args.url)

    try:
        subprocess.run(cmd, check=True)
        print("\n下載完成！音訊檔案 (.mp3) 與中繼資料 (.info.json) 已保存於當前目錄。")
        print("後續請由 AI Agent 根據這些資訊（如標題、頻道名稱）判斷並建立對應的分類資料夾，然後進行整理。")
    except subprocess.CalledProcessError as e:
        print(f"下載失敗: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
