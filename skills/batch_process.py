# /// script
# dependencies = ["python-dotenv"]
# ///
"""
批次處理腳本 v2：依序下載→整理→轉譯所有指定影片

Step 1 邏輯（2026-08-14 更新）：
  1. 先用 yt-dlp --write-info-json --no-download 抓 metadata
  2. 檢查是否有字幕（subtitles / requested_subtitles）
     → 有字幕：yt-dlp --write-subs --skip-download --sub-langs zh 擷取
     → 無字幕：yt-dlp -x --audio-format mp3 下載音頻 → 轉譯

Cookies 在啟動時一次性讀入記憶體，全程重複使用。
成功失敗皆自動寫入 download_log.md。

用法：uv run skills/batch_process.py
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

# ─── 影片 URL 列表（僅未下載的）────────────────────────────────────
VIDEO_URLS = [
    # 2026-09-29 單支處理（用戶請求）每日要聞
    "https://www.youtube.com/watch?v=1ly-LoGUfmY",
    # 2026-09-26 新增（用戶請求）會員直播
    "https://www.youtube.com/watch?v=Qr-91HWZ7mM",
    # 2026-09-16 新增（用戶請求）
    "https://www.youtube.com/watch?v=oqHAV1X1zgc",
    # 2026-09-16 新增（用戶請求）
    "https://www.youtube.com/watch?v=CER6TEfryT8",
    "https://www.youtube.com/watch?v=8s7D9GmHPEU",
    "https://www.youtube.com/watch?v=5NcvOCdPMhc",
    "https://www.youtube.com/watch?v=UEXO8r0KXkI",
    "https://www.youtube.com/watch?v=RMFs18uXZxg",
    "https://www.youtube.com/watch?v=YGmAbhAPiLc",
    # 2026-09-06 新增（用戶請求）
    "https://www.youtube.com/live/ztXqwMR6wnY",
    # 2026-09-04 新增（用戶請求）
    "https://www.youtube.com/watch?v=WHhVEF1rNvU",
    "https://www.youtube.com/watch?v=ikBq2S6xvhU",
    # 2026-08-31 單支處理
    "https://www.youtube.com/watch?v=_o2C1XwEhoo",
    # 2026-09-03 新增（用戶請求）
    "https://www.youtube.com/watch?v=cZsVyVvoAqo",
    # 2026-08-29 新增
    "https://www.youtube.com/watch?v=Kp2wRktr8Rg",
    "https://www.youtube.com/watch?v=wyBM09F7rtg",
    "https://www.youtube.com/watch?v=irmbS8P3Eh0",
]

# ─── 分類路由：URL → 存放分類目錄（從 docs 資料夾自動生成）───────────────
CATEGORY_MAP = {
    # 2026-09-29 單支處理（用戶請求）
    "https://www.youtube.com/watch?v=dwAoGcHfkII": "每日要聞",
    "https://www.youtube.com/watch?v=1ly-LoGUfmY": "每日要聞",
    # 2026-09-26 新增（用戶請求）會員直播
    "https://www.youtube.com/watch?v=Qr-91HWZ7mM": "會員直播",
    # 2026-09-16 新增（用戶請求）
    "https://www.youtube.com/watch?v=oqHAV1X1zgc": "每日要聞",
    # 2026-09-16 新增（用戶請求）
    "https://www.youtube.com/watch?v=CER6TEfryT8": "每日要聞",
    "https://www.youtube.com/watch?v=8s7D9GmHPEU": "每日要聞",
    "https://www.youtube.com/watch?v=5NcvOCdPMhc": "每日要聞",
    "https://www.youtube.com/watch?v=UEXO8r0KXkI": "每日要聞",
    "https://www.youtube.com/watch?v=RMFs18uXZxg": "每日要聞",
    "https://www.youtube.com/watch?v=YGmAbhAPiLc": "會員直播",
    # 2026-09-06 新增（用戶請求）
    "https://www.youtube.com/live/ztXqwMR6wnY": "每日要聞",
    # 2026-09-04 新增（用戶請求）
    "https://www.youtube.com/watch?v=WHhVEF1rNvU": "會員直播",
    "https://www.youtube.com/watch?v=ikBq2S6xvhU": "每日要聞",
    # 每日要聞 (2026-09-03)
    "https://www.youtube.com/watch?v=cZsVyVvoAqo": "每日要聞",
    # 地緣政治 (2支)
    "https://www.youtube.com/watch?v=dI8SPFRQPDQ": "地緣政治",
    "https://www.youtube.com/watch?v=q8qbKqScIIw": "地緣政治",
    # 會員直播 (48支)
    "https://www.youtube.com/watch?v=hRSL2EPVpfI": "會員直播",
    # 會員直播 (47支)
    "https://www.youtube.com/watch?v=-qPojdM6_hI": "會員直播",
    "https://www.youtube.com/watch?v=0vgFdvHUqgk": "會員直播",
    "https://www.youtube.com/watch?v=1HbseyIt9WA": "會員直播",
    "https://www.youtube.com/watch?v=3UImMWaGPto": "會員直播",
    "https://www.youtube.com/watch?v=591SwbfOcdM": "會員直播",
    "https://www.youtube.com/watch?v=7NOxcsexRAc": "會員直播",
    "https://www.youtube.com/watch?v=8ZDG-PDlx7c": "會員直播",
    "https://www.youtube.com/watch?v=8p9wZ_2a5AY": "會員直播",
    "https://www.youtube.com/watch?v=A2CfD0VlNc4": "會員直播",
    "https://www.youtube.com/watch?v=DlzOcUfWpfY": "會員直播",
    "https://www.youtube.com/watch?v=IaFBitWBdZc": "會員直播",
    "https://www.youtube.com/watch?v=LjBB-gxvQTI": "會員直播",
    "https://www.youtube.com/watch?v=MWOvp6VoXks": "會員直播",
    "https://www.youtube.com/watch?v=NskA3C0c9Lo": "會員直播",
    "https://www.youtube.com/watch?v=OEF9ce61_So": "會員直播",
    "https://www.youtube.com/watch?v=PByCVMUhPvk": "會員直播",
    "https://www.youtube.com/watch?v=REzgDl4LhQE": "會員直播",
    "https://www.youtube.com/watch?v=RRdinfbKyu0": "會員直播",
    "https://www.youtube.com/watch?v=U0MZjMjJhDw": "會員直播",
    "https://www.youtube.com/watch?v=Uh2Q2yydfuE": "會員直播",
    "https://www.youtube.com/watch?v=aEYcdVScnWI": "會員直播",
    "https://www.youtube.com/watch?v=aNiIpejB_D8": "會員直播",
    "https://www.youtube.com/watch?v=abbAxwubDek": "會員直播",
    "https://www.youtube.com/watch?v=alWK2KL7qo8": "會員直播",
    "https://www.youtube.com/watch?v=bw5Thfe6H9M": "會員直播",
    "https://www.youtube.com/watch?v=e4IQveWmMEk": "會員直播",
    "https://www.youtube.com/watch?v=eWtX9HLWutI": "會員直播",
    "https://www.youtube.com/watch?v=et9I8BX9RBM": "會員直播",
    "https://www.youtube.com/watch?v=fW5-rDLOzc8": "會員直播",
    "https://www.youtube.com/watch?v=gUFO4HgCxjU": "會員直播",
    "https://www.youtube.com/watch?v=gYI_Lzs8Few": "會員直播",
    "https://www.youtube.com/watch?v=heQ7MXBnac8": "會員直播",
    "https://www.youtube.com/watch?v=jLEBFgxKndk": "會員直播",
    "https://www.youtube.com/watch?v=jr6JJ2gygO4": "會員直播",
    "https://www.youtube.com/watch?v=kBDAbIbbepc": "會員直播",
    "https://www.youtube.com/watch?v=oV351WZsf5s": "會員直播",
    "https://www.youtube.com/watch?v=p1nX2m2Di1c": "會員直播",
    "https://www.youtube.com/watch?v=rGDmDptih6k": "會員直播",
    "https://www.youtube.com/watch?v=sCNJYGDIAoo": "會員直播",
    "https://www.youtube.com/watch?v=sVjkW3O__qo": "會員直播",
    "https://www.youtube.com/watch?v=tfqu90W7_t0": "會員直播",
    "https://www.youtube.com/watch?v=uHQs-kIsB64": "會員直播",
    "https://www.youtube.com/watch?v=vRYaGKBMlUo": "會員直播",
    "https://www.youtube.com/watch?v=viKjUUw_Gwo": "會員直播",
    "https://www.youtube.com/watch?v=wtTVDWW_dfU": "會員直播",
    "https://www.youtube.com/watch?v=xi59m8P-BHY": "會員直播",
    "https://www.youtube.com/watch?v=yWKbmt4wBXY": "會員直播",
    # 每日要聞 (24支)
    "https://www.youtube.com/watch?v=27mye39aYCg": "每日要聞",
    "https://www.youtube.com/watch?v=2O4VsfkiPNk": "每日要聞",
    "https://www.youtube.com/watch?v=A57SeLbDLPk": "每日要聞",
    "https://www.youtube.com/watch?v=Du_zgzHwrS0": "每日要聞",
    "https://www.youtube.com/watch?v=GWSKT6uVN0Y": "每日要聞",
    "https://www.youtube.com/watch?v=H991IN1LZpM": "每日要聞",
    "https://www.youtube.com/watch?v=O3aWys1FXHI": "每日要聞",
    "https://www.youtube.com/watch?v=OC225e0zJpY": "每日要聞",
    "https://www.youtube.com/watch?v=PrhptxAClcc": "每日要聞",
    "https://www.youtube.com/watch?v=SHYNuMvm1wc": "每日要聞",
    "https://www.youtube.com/watch?v=T7tLmRLSYys": "每日要聞",
    "https://www.youtube.com/watch?v=V-5xmDlKxQk": "每日要聞",
    "https://www.youtube.com/watch?v=Zw6CUueiFxA": "每日要聞",
    "https://www.youtube.com/watch?v=_gOMWQLWyDM": "每日要聞",
    "https://www.youtube.com/watch?v=cnVX8Afa-T4": "每日要聞",
    "https://www.youtube.com/watch?v=e0kXm0ix7C8": "每日要聞",
    "https://www.youtube.com/watch?v=mUptjefNQqA": "每日要聞",
    "https://www.youtube.com/watch?v=n5EhVA6mY8A": "每日要聞",
    "https://www.youtube.com/watch?v=rpPq818k2yQ": "每日要聞",
    "https://www.youtube.com/watch?v=spUu0FzSuVo": "每日要聞",
    "https://www.youtube.com/watch?v=vZ8BbItjcrI": "每日要聞",
    "https://www.youtube.com/watch?v=wkK_tR_Dzw4": "每日要聞",
    "https://www.youtube.com/watch?v=yDWe27mDNDE": "每日要聞",
    "https://www.youtube.com/watch?v=yR5MhHjc5Zo": "每日要聞",
    # 2026-08-31 單支處理
    "https://www.youtube.com/watch?v=_o2C1XwEhoo": "每日要聞",
}

PROJECT_ROOT = "E:/AI Training/cui-member-skill"
BATCH_LOG   = f"{PROJECT_ROOT}/docs/batch_log.md"
DOWNLOAD_LOG = f"{PROJECT_ROOT}/docs/download_log.md"

# ─── 全域 Cookies ──────────────────────────────────────────────────────
_COOKIES_CONTENT = None
_COOKIES_FILE   = None


def load_cookies():
    global _COOKIES_CONTENT, _COOKIES_FILE
    src = os.path.join(PROJECT_ROOT, "Cookies", "cookies.txt")
    with open(src, "r", encoding="utf-8") as f:
        _COOKIES_CONTENT = f.read()
    fd, _COOKIES_FILE = tempfile.mkstemp(suffix=".txt", prefix="ytcookies_")
    os.close(fd)
    with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(_COOKIES_CONTENT)
    log(f"Cookies 載入完成（{len(_COOKIES_CONTENT)} 字元）→ {_COOKIES_FILE}")


def refresh_cookies():
    global _COOKIES_CONTENT
    src = os.path.join(PROJECT_ROOT, "Cookies", "cookies.txt")
    with open(src, "r", encoding="utf-8") as f:
        _COOKIES_CONTENT = f.read()
    if _COOKIES_FILE:
        with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(_COOKIES_CONTENT)
    log_warn("Cookies 已刷新（cookies.txt → 暫存檔），下載失敗可能是 cookies 已過期")


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(BATCH_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_warn(msg: str):
    """寫入 log 並同時輸出至 stderr，確保 CI/自動化能看到警告。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [WARN] {msg}"
    print(line, file=sys.stderr)
    with open(BATCH_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def run_cmd(cmd: str, timeout=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout, cwd=PROJECT_ROOT)
    return r.returncode, r.stdout, r.stderr


def cleanup_temp():
    for pat in ["*.mp3", "*.webm", "*.info.json", "*.txt", "*.vtt", "*.srt", "*.ass"]:
        for f in glob.glob(os.path.join(PROJECT_ROOT, pat)):
            if os.path.basename(f) == "cookies.txt":
                continue
            try:
                os.remove(f)
            except Exception:
                pass


def get_video_info(info_path: str) -> tuple:
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (
            data.get("title", ""),
            data.get("upload_date", ""),
            data.get("duration", 0),
            data.get("subtitles") or {},
            data.get("requested_subtitles") or {},
        )
    except Exception:
        return "", "", 0, {}, {}


def has_subtitles(video_info: dict) -> bool:
    """檢查是否有可用的字幕（YouTube 自動字幕或上傳字幕）"""
    subs = video_info.get("subtitles") or {}
    req  = video_info.get("requested_subtitles") or {}
    return bool(subs or req)


def srt_to_plaintext(srt_path: str) -> str:
    """將 SRT 檔案轉為純文字（移除時間軸與序號）"""
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        with open(srt_path, "r", encoding="latin-1") as f:
            content = f.read()

    lines = []
    for line in content.splitlines():
        # 跳過時間軸行（包含 -->）
        if "-->" in line:
            continue
        # 跳過序號行（純數字）
        if re.match(r"^\d+$", line.strip()):
            continue
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    # 句末加分段空行
    result = []
    SENTENCE_END = ("。", "！", "？", "…", "!", "?")
    for line in lines:
        result.append(line)
        if line.endswith(SENTENCE_END):
            result.append("")
    return "\n".join(result)


def update_download_log(url: str, title: str, video_id: str,
                        category: str, method: str, success: bool, note: str = ""):
    """
    自動寫入 download_log.md
    method: "字幕" | "MP3+轉譯" | "已存在"
    """
    ts = datetime.now().strftime("%Y-%m-%d")
    status = "✅" if success else "❌"
    entry = f"\n**{ts}**\n"
    entry += f"- {status} [{category}] {title} | {video_id} | {method}"
    if note:
        entry += f" | {note}"
    entry += f" | [影片](https://www.youtube.com/watch?v={video_id})"

    with open(DOWNLOAD_LOG, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


# ─── 核心：單支影片處理 ────────────────────────────────────────────────

def process_video(url: str) -> tuple:
    """
    處理流程：
      Step 1a: 只抓 metadata（不下載音頻）
      Step 1b: 檢查字幕
        → 有字幕：yt-dlp --write-subs --skip-download 擷取
        → 無字幕：下載 MP3 + 轉譯
    成功回傳 (True, date_str, duration, method, video_id, title, category)
    """
    vid_id   = url.split("=")[-1]
    category = CATEGORY_MAP.get(url, "會員直播")
    cleanup_temp()

    # ─── Step 1a: 只抓 metadata ────────────────────────────────────
    log(f"[{vid_id}] 抓取 metadata...")
    out_template = os.path.join(PROJECT_ROOT, "%(title)s [%(id)s].%(ext)s")

    code, stdout, stderr = run_cmd(
        f'uv run yt-dlp --write-info-json --no-download '
        f'--cookies "{_COOKIES_FILE}" '
        f'-o "{out_template}" "{url}"',
        timeout=120
    )
    if code != 0:
        log(f"  [FAIL] metadata 抓取失敗")
        log(f"  {stderr[-300:]}")
        return False, None, 0, "metadata_failed", vid_id, "", category

    # 找 info.json
    info_files = glob.glob(os.path.join(PROJECT_ROOT, "*.info.json"))
    if not info_files:
        log(f"  [FAIL] 未找到 info.json")
        return False, None, 0, "no_info", vid_id, "", category

    info_local = info_files[0]
    title, date_str, duration, _, _ = get_video_info(info_local)

    if not date_str:
        # 從標題或時間戳推斷
        m = re.search(r"(\d{4})(\d{2})(\d{2})", title or info_local)
        date_str = (f"{m.group(1)}{m.group(2)}{m.group(3)}"
                    if m else datetime.now().strftime("%Y%m%d"))

    out_dir = os.path.join(PROJECT_ROOT, "docs", category, date_str)
    ensure_dir(out_dir)

    # 移動 info.json 到目標目錄（覆寫已存在的）
    dst_info = os.path.join(out_dir, "audio.info.json")
    if os.path.exists(info_local):
        if os.path.exists(dst_info):
            os.remove(dst_info)
        os.rename(info_local, dst_info)

    # ─── Step 1b: 檢查字幕 ────────────────────────────────────────
    log(f"[{vid_id}] 檢查字幕...")
    title_raw, _, duration_raw, subs, req_subs = get_video_info(dst_info)
    has_sub = has_subtitles({"subtitles": subs, "requested_subtitles": req_subs})

    method = ""
    txt_path = os.path.join(out_dir, "audio.txt")

    if has_sub:
        # 有字幕：擷取
        log(f"  字幕偵測到，使用字幕擷取（不下載 MP3）...")
        code2, _, stderr2 = run_cmd(
            f'uv run yt-dlp --write-subs --skip-download '
            f''
            f'--sub-langs zh --sub-format vtt '
            f'--cookies "{_COOKIES_FILE}" '
            f'-o "{out_template}" "{url}"',
            timeout=120
        )
        if code2 == 0:
            # 找字幕檔（SRT/VTT）
            sub_files = (
                glob.glob(os.path.join(PROJECT_ROOT, "*.srt")) +
                glob.glob(os.path.join(PROJECT_ROOT, "*.vtt"))
            )
            if sub_files:
                raw_sub = sub_files[0]
                text = srt_to_plaintext(raw_sub)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                os.remove(raw_sub)
                method = "字幕（zh）"
                log(f"  [OK] 字幕擷取完成 → audio.txt")
            else:
                method = "字幕（擷取失敗）"
                log(f"  [WARN] 字幕檔未找到")
        else:
            method = "字幕（失敗→降級Whisper）"
            log(f"  [WARN] 字幕擷取失敗，降級至 Whisper: {stderr2[-200:]}")
            has_sub = False  # 降級

    if not has_sub or not os.path.exists(txt_path):
        # 無字幕：下載 MP3 並轉譯
        if has_sub and not os.path.exists(txt_path):
            pass  # 字幕擷取失敗後，降級轉譯
        elif os.path.exists(txt_path) or os.path.exists(os.path.join(out_dir, "audio.mp3")):
            method = "已存在"
            log(f"  [SKIP] audio.txt 或 audio.mp3 已存在")
            update_download_log(url, title or dst_info, vid_id, category, "已存在", True)
            return True, date_str, duration_raw, "already_exists", vid_id, title, category

        log(f"  無字幕，下載 MP3 + Whisper 轉譯...")
        code3, stdout3, stderr3 = run_cmd(
            f'uv run yt-dlp -x --audio-format mp3 '
            f'--cookies "{_COOKIES_FILE}" '
            f'-o "{out_template}" "{url}"',
            timeout=300
        )
        if code3 != 0:
            refresh_cookies()
            code3, stdout3, stderr3 = run_cmd(
                f'uv run yt-dlp -x --audio-format mp3 '
                f''
                f'--cookies "{_COOKIES_FILE}" '
                f'-o "{out_template}" "{url}"',
                timeout=300
            )
            if code3 != 0:
                log_warn(f"MP3 下載第二次重試失敗：{url}")
                log_warn(f"請至 Cookies/cookies.txt 更新 cookies 後再執行")
                log_warn(f"影片：{title or vid_id}")
                update_download_log(url, title or vid_id, vid_id, category, "MP3下載失敗（cookies可能過期）", False)
                return False, date_str, 0, "mp3_failed", vid_id, title, category

        mp3_files = glob.glob(os.path.join(PROJECT_ROOT, "*.mp3"))
        if not mp3_files:
            log(f"  [FAIL] MP3 未找到")
            return False, date_str, 0, "no_mp3", vid_id, title, category

        mp3_src = mp3_files[0]
        dst_mp3 = os.path.join(out_dir, "audio.mp3")
        if os.path.exists(dst_mp3):
            os.remove(dst_mp3)
        os.rename(mp3_src, dst_mp3)
        method = "MP3+Whisper"

        # ── 轉譯（可透過 SKIP_WHISPER=1 跳過）───────────────────────
        if os.getenv("SKIP_WHISPER", "0") == "1":
            log(f"  [SKIP] 轉譯已跳過（SKIP_WHISPER=1）")
            update_download_log(url, title or vid_id, vid_id, category, "MP3下載（跳過轉譯）", True)
            log(f"  [完成] docs/{category}/{date_str}/")
            return True, date_str, duration_raw, "MP3下載（跳過轉譯）", vid_id, title, category

        log(f"  轉譯中 (Whisper GPU)...")
        transcribe_script = os.path.join(PROJECT_ROOT, "skills", "transcribe_gpu.py")
        anaconda_python = r"D:\anaconda3\python.exe"
        code4, _, stderr4 = run_cmd(
            f'"{anaconda_python}" "{transcribe_script}" "{dst_mp3}"',
            timeout=int(duration_raw * 1.5) if duration_raw else 3600
        )
        if code4 != 0:
            log(f"  [FAIL] 轉譯失敗: {stderr4[-200:]}")
            update_download_log(url, title or vid_id, vid_id, category, "MP3+轉譯失敗", False)
            return False, date_str, duration_raw, "transcribe_failed", vid_id, title, category

        # 移動 txt
        txt_files = glob.glob(os.path.join(PROJECT_ROOT, "*.txt"))
        if txt_files:
            os.rename(txt_files[0], txt_path)
        log(f"  [OK] 轉譯完成 → audio.txt")

    # 成功
    update_download_log(url, title or vid_id, vid_id, category, method, True)
    log(f"  [完成] docs/{category}/{date_str}/")
    return True, date_str, duration_raw, method, vid_id, title, category


# ─── 主程式 ────────────────────────────────────────────────────────────

def main():
    os.makedirs(f"{PROJECT_ROOT}/docs", exist_ok=True)
    load_cookies()

    with open(BATCH_LOG, "w", encoding="utf-8") as f:
        f.write(f"# 批次處理日誌（v2 — 字幕優先）\n"
                 f"# 開始：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    total   = len(VIDEO_URLS)
    success = 0
    failed  = []

    log(f"開始批次處理，共 {total} 支")

    for i, url in enumerate(VIDEO_URLS, 1):
        vid_id = url.split("=")[-1]
        log(f"=== [{i}/{total}] {vid_id} ===")
        ok, *rest = process_video(url)
        if ok:
            success += 1
        else:
            failed.append(url)
        log(f"進度：{success}/{total} 成功，{len(failed)} 失敗\n")

    log("=== 完成 ===")
    log(f"成功：{success}/{total}，失敗：{len(failed)}")
    for u in failed:
        log(f"  失敗：{u}")

    # 清理暫存 cookies
    global _COOKIES_FILE
    if _COOKIES_FILE and os.path.exists(_COOKIES_FILE):
        try:
            os.remove(_COOKIES_FILE)
        except Exception:
            pass

    print(f"\n完成！成功 {success}/{total}")


if __name__ == "__main__":
    main()
