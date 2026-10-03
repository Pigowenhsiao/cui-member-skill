# /// script
# dependencies = ["python-dotenv"]
# ///
"""
批次下載腳本：只下載不轉譯，避免 Cookies 過期
Cookies 在啟動時一次性讀入記憶體
用法：uv run python skills/batch_download_only.py
"""
import os
import sys
import json
import glob
import subprocess
import re
import tempfile
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 尚未下載的影片 URL（已下載的已移除）
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=e4IQveWmMEk",
    "https://www.youtube.com/watch?v=heQ7MXBnac8",
    "https://www.youtube.com/watch?v=kBDAbIbbepc",
    "https://www.youtube.com/watch?v=591SwbfOcdM",
    "https://www.youtube.com/watch?v=aNiIpejB_D8",
    "https://www.youtube.com/watch?v=fW5-rDLOzc8",
    "https://www.youtube.com/watch?v=1HbseyIt9WA",
    "https://www.youtube.com/watch?v=U0MZjMjJhDw",
    "https://www.youtube.com/watch?v=vRYaGKBMlUo",
    "https://www.youtube.com/watch?v=wtTVDWW_dfU",
    "https://www.youtube.com/watch?v=alWK2KL7qo8",
    "https://www.youtube.com/watch?v=3UImMWaGPto",
    "https://www.youtube.com/watch?v=DlzOcUfWpfY",
    "https://www.youtube.com/watch?v=gUFO4HgCxjU",
    "https://www.youtube.com/watch?v=7NOxcsexRAc",
    "https://www.youtube.com/watch?v=oV351WZsf5s",
    "https://www.youtube.com/watch?v=uHQs-kIsB64",
    "https://www.youtube.com/watch?v=tfqu90W7_t0",
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = f"{PROJECT_ROOT}/docs/download_log.md"
_COOKIES_FILE = None

def load_cookies():
    global _COOKIES_FILE
    src = os.path.join(PROJECT_ROOT, "Cookies", "cookies.txt")
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    fd, _COOKIES_FILE = tempfile.mkstemp(suffix=".txt", prefix="ytcookies_")
    os.close(fd)
    with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[INIT] Cookies loaded ({len(content)} chars)")

def refresh_cookies():
    global _COOKIES_FILE
    src = os.path.join(PROJECT_ROOT, "Cookies", "cookies.txt")
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    if _COOKIES_FILE and os.path.exists(_COOKIES_FILE):
        with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"[REFRESH] Cookies updated ({len(content)} chars)")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def cleanup():
    for pattern in ["*.mp3", "*.webm", "*.info.json", "*.txt"]:
        for f in glob.glob(os.path.join(PROJECT_ROOT, pattern)):
            if os.path.basename(f) == "cookies.txt":
                continue
            try: os.remove(f)
            except: pass

def run_cmd(cmd, timeout=None):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_ROOT)

def main():
    os.makedirs(f"{PROJECT_ROOT}/docs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n# --- 新批次 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    load_cookies()

    total = len(VIDEO_URLS)
    success = 0
    failed = []

    log(f"開始下載，共 {total} 支")

    for i, url in enumerate(VIDEO_URLS, 1):
        vid = url.split("=")[-1]
        cleanup()

        log(f"[{i}/{total}] 下載：{vid}")
        r = run_cmd(
            f'uv run yt-dlp -x --audio-format mp3 --cookies "{_COOKIES_FILE}" '
            f'-o "%(title)s [%(id)s].%(ext)s" --write-info-json "{url}"',
            timeout=120
        )

        if r.returncode != 0:
            refresh_cookies()
            r = run_cmd(
                f'uv run yt-dlp -x --audio-format mp3 --cookies "{_COOKIES_FILE}" '
                f'-o "%(title)s [%(id)s].%(ext)s" --write-info-json "{url}"',
                timeout=120
            )
            if r.returncode != 0:
                log(f"  [FAIL] {r.stderr[-200:]}")
                failed.append(url)
                continue

        mp3s = glob.glob(os.path.join(PROJECT_ROOT, "*.mp3"))
        infos = glob.glob(os.path.join(PROJECT_ROOT, "*.info.json"))
        if not mp3s:
            log(f"  [WARN] 無 MP3")
            failed.append(url)
            continue

        mp3_f = mp3s[0]
        info_f = infos[0] if infos else None

        if info_f:
            with open(info_f, encoding="utf-8") as f:
                data = json.load(f)
            date_str = data.get("upload_date", "")
        else:
            m = re.search(r"(\d{4})(\d{2})(\d{2})", mp3_f)
            date_str = f"{m.group(1)}{m.group(2)}{m.group(3)}" if m else ""

        out_dir = os.path.join(PROJECT_ROOT, "docs", "會員直播", date_str)
        os.makedirs(out_dir, exist_ok=True)

        for dst in [f"{out_dir}/audio.mp3", f"{out_dir}/audio.info.json"]:
            if os.path.exists(dst):
                os.remove(dst)

        os.rename(mp3_f, f"{out_dir}/audio.mp3")
        if info_f: os.rename(info_f, f"{out_dir}/audio.info.json")

        log(f"  [OK] {date_str}")
        success += 1

    log(f"完成：{success}/{total}，失敗 {len(failed)}")
    for url in failed:
        log(f"  FAIL: {url}")

    if _COOKIES_FILE:
        try: os.remove(_COOKIES_FILE)
        except: pass

    print(f"\n=== 完成：{success}/{total} ===")

if __name__ == "__main__":
    main()
