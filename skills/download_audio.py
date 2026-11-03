# /// script
# dependencies = [
#     "python-dotenv",
#     "yt-dlp",
# ]
# ///
import os
import sys
import subprocess
import argparse
from dotenv import load_dotenv

from path_utils import PROJECT_ROOT, project_path
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

    parser = argparse.ArgumentParser(description="下載 YouTube 音訊並保留標題等中繼資料 (Metadata)")
    parser.add_argument("url", help="YouTube 影片或播放清單 URL")
    parser.add_argument("--cookies", help="Cookies 檔案路徑", default=None)
    parser.add_argument("--browser", help="從指定的瀏覽器直接讀取 Cookies (例如 firefox, chrome, safari, edge)", default=None)
    parser.add_argument("--output-dir", help="輸出資料夾（預設為專案根目錄）", default=None)
    args = parser.parse_args()

    output_dir = project_path(args.output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s.%(ext)s")

    load_dotenv(PROJECT_ROOT / ".env")

    browser = args.browser if args.browser is not None else os.environ.get("COOKIES_BROWSER", "")
    if browser and browser.lower() in ("none", "false", ""):
        browser = None

    cookies_file = args.cookies if args.cookies is not None else os.environ.get("COOKIES_PATH", "cookies.txt")
    cookie_path = project_path(cookies_file) if cookies_file and cookies_file.lower() not in ("none", "false", "") else None

    print(f"正在從 {args.url} 下載音訊...")
    if cookie_path and cookie_path.is_file():
        print(f"使用 Cookies 檔案: {cookie_path}")
    elif browser:
        print(f"自動讀取瀏覽器 Cookies: {browser}")
    else:
        print("未找到或未使用 Cookies 檔案。")

    # yt-dlp 命令：
    # -x, --audio-format mp3: 提取音訊並轉為 mp3
    # --write-info-json: 將影片標題、頻道等中繼資料寫入 JSON，方便 AI Agent 後續分析
    # -o: 指定輸出檔名格式
    # --js-runtimes node: 使用 Node.js 作為 JavaScript 運行時（用於解決 YouTube n challenge）
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--windows-filenames",
        "-x",
        "--audio-format",
        "mp3",
        "--write-info-json",
        "-o",
        output_template,
        "--js-runtimes",
        "node",
        "--remote-components",
        "ejs:github",
        "--extractor-args",
        "youtube:player_client=web_embedded,android,ios"
    ]
    
    if cookie_path and cookie_path.is_file():
        cmd.extend(["--cookies", str(cookie_path)])
    elif browser:
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(args.url)

    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        from log_download import add_log
        add_log(args.url)
        print("\n下載完成！音訊檔案 (.mp3) 與中繼資料 (.info.json) 已保存於輸出資料夾。")
    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower() if e.stderr else ""
        if any(keyword in stderr_lower for keyword in ["sign in", "bot", "cookie", "member", "private", "members-only"]):
            print(f"\n[COOKIE_ERROR] YouTube 拒絕存取。Cookie 可能無效、過期或未提供。\n詳細錯誤: {e.stderr}", file=sys.stderr)
        else:
            print(f"下載失敗: {e.stderr if e.stderr else e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
