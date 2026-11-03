# /// script
# dependencies = [
#     "python-dotenv",
#     "openai",
#     "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#     "faster-whisper",
#     "mutagen",
# ]
# ///
import os
import sys
import argparse
import platform
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

try:
    from .path_utils import PROJECT_ROOT, project_path
except ImportError:
    from path_utils import PROJECT_ROOT, project_path

# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------

def get_audio_duration(audio_path: str) -> float:
    """傳回音訊長度（秒）。優先使用 mutagen，失敗則嘗試 ffprobe。"""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(audio_path)
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception:
        pass

    # fallback: ffprobe
    try:
        import subprocess, json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", audio_path],
            capture_output=True, text=True, check=True
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        pass

    return 0.0


def ensure_file_under_limit(audio_path: str, max_bytes: int = 24 * 1024 * 1024) -> tuple[str, bool]:
    """若音訊檔案超過 max_bytes，自動使用 ffmpeg 動態計算位元率並壓縮為單聲道 16kHz mp3 暫存檔。"""
    current_size = os.path.getsize(audio_path)
    if current_size <= max_bytes:
        return audio_path, False

    print(f"檔案大小 ({current_size} bytes) 超過 24MB API 限制，自動使用 ffmpeg 進行壓縮...", file=sys.stderr)
    duration = get_audio_duration(audio_path)
    
    # 計算位元率 (預留 10% 安全邊界)
    if duration > 0:
        target_bps = (max_bytes * 8 * 0.9) / duration
        bitrate_kbps = max(16, min(64, int(target_bps / 1000)))
    else:
        bitrate_kbps = 32

    print(f"動態調降位元率為: {bitrate_kbps}k (採樣率 16kHz 單聲道)", file=sys.stderr)

    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "16000", "-b:a", f"{bitrate_kbps}k", temp_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        compressed_size = os.path.getsize(temp_path)
        print(f"壓縮成功，壓縮後大小: {compressed_size} bytes", file=sys.stderr)
        return temp_path, True
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError(f"ffmpeg 壓縮失敗: {e}")



def format_segments(segments: list) -> str:
    """
    將片段列表整理為字串並返回。
    - 各片段以換行分隔
    - 以句點（。！？…）結尾的片段後方加插空行
    """
    SENTENCE_END = ("。", "！", "？", "…", "!", "?")
    lines = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(text)
        if text.endswith(SENTENCE_END):
            lines.append("")   # 句尾後加插空行
    return "\n".join(lines)


def print_progress(current_sec: float, total_sec: float, prefix: str = "") -> None:
    """將目前進度輸出至主控台（stderr）。"""
    if total_sec <= 0:
        return
    pct = min(current_sec / total_sec * 100, 100.0)
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    msg = f"\r{prefix}[{bar}] {pct:5.1f}%  ({current_sec:.0f}s / {total_sec:.0f}s)"
    print(msg, end="", flush=True, file=sys.stderr)


# ---------------------------------------------------------------------------
# 轉寫後端
# ---------------------------------------------------------------------------

def transcribe_local(audio_path: str) -> str:
    is_mac_arm = platform.system() == "Darwin" and platform.machine() == "arm64"
    total_sec = get_audio_duration(audio_path)

    if is_mac_arm:
        print(f"偵測到 Apple Silicon macOS，使用本地 mlx-whisper 進行 GPU 加速語音識別 (音訊: {audio_path})...")
        import mlx_whisper
        model = os.getenv("WHISPER_MODEL", "mlx-community/whisper-medium-mlx-8bit")
        print(f"載入模型: {model}")

        # mlx_whisper 在 verbose=True 時會將 segment 輸出至 stdout。
        # 為了自行取得進度，設 verbose=False 並遍歷 segments。
        raw = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=model,
            language="zh",
            verbose=False       # 自行顯示進度，因此設為 False
        )
        segments = raw.get("segments", [])
        seg_dicts = []
        for seg in segments:
            start = seg.get("start", 0.0)
            end   = seg.get("end",   0.0)
            text  = seg.get("text",  "")
            print_progress(end, total_sec, prefix="轉譯進度 ")
            print(f"\n[{start:06.1f}s -> {end:06.1f}s] {text.strip()}", file=sys.stderr)
            seg_dicts.append({"text": text, "start": start, "end": end})

        print(file=sys.stderr)  # 改行
        return format_segments(seg_dicts)

    else:
        print(f"非 Apple Silicon 環境，使用 CPU 版 faster-whisper (型號: medium) 進行語音識別 (音訊: {audio_path})...")
        from faster_whisper import WhisperModel

        model = WhisperModel("medium", device="cpu", compute_type="int8")
        segments_gen, info = model.transcribe(audio_path, beam_size=5, language="zh")
        print(f"偵測語言為 '{info.language}'，信心度 {info.language_probability:.2f}")

        seg_dicts = []
        for seg in segments_gen:
            print_progress(seg.end, total_sec, prefix="轉譯進度 ")
            print(f"\n[{seg.start:06.1f}s -> {seg.end:06.1f}s] {seg.text.strip()}", file=sys.stderr)
            seg_dicts.append({"text": seg.text, "start": seg.start, "end": seg.end})

        print(file=sys.stderr)  # 改行
        return format_segments(seg_dicts)


def transcribe_openai(audio_path: str) -> str:
    print(f"使用 OpenAI API 進行語音識別 (音訊: {audio_path})...")
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("未設定 OPENAI_API_KEY 環境變數。")

    target_path, is_temp = ensure_file_under_limit(audio_path)
    try:
        with open(target_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="zh",
                response_format="verbose_json"  # 取得片段資訊
            )
    finally:
        if is_temp and os.path.exists(target_path):
            os.remove(target_path)

    # verbose_json 時會包含 segments
    if hasattr(transcript, "segments") and transcript.segments:
        seg_dicts = [{"text": s.text} for s in transcript.segments]
        return format_segments(seg_dicts)
    return transcript.text


def transcribe_azure(audio_path: str) -> str:
    print(f"使用 Azure OpenAI API 進行語音識別 (音訊: {audio_path})...")
    from openai import AzureOpenAI

    api_key       = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint      = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version   = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    deployment    = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    if not all([api_key, endpoint, deployment]):
        raise ValueError("請檢查 Azure 相關環境變數 (API_KEY, ENDPOINT, DEPLOYMENT_NAME) 是否設定完整。")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )

    target_path, is_temp = ensure_file_under_limit(audio_path)
    try:
        with open(target_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model=deployment,
                file=f,
                language="zh",
                response_format="verbose_json"
            )
    finally:
        if is_temp and os.path.exists(target_path):
            os.remove(target_path)

    if hasattr(transcript, "segments") and transcript.segments:
        seg_dicts = [{"text": s.text} for s in transcript.segments]
        return format_segments(seg_dicts)
    return transcript.text



# ---------------------------------------------------------------------------
# 程式進入點
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="語音文字稿轉換工具 (支援 Local, OpenAI API, Azure OpenAI)")
    parser.add_argument("audio_file", help="要轉換的音訊檔案路徑 (例如 .mp3)")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    mode = os.getenv("WHISPER_MODE", "local").lower()
    audio_path = project_path(args.audio_file)

    if not audio_path.is_file():
        print(f"錯誤: 找不到音訊檔案 {audio_path}", file=sys.stderr)
        sys.exit(1)

    try:
        if mode == "local":
            text = transcribe_local(str(audio_path))
        elif mode == "openai":
            text = transcribe_openai(str(audio_path))
        elif mode == "azure":
            text = transcribe_azure(str(audio_path))
        else:
            raise ValueError(f"未知的 WHISPER_MODE: {mode}。請設定為 local, openai 或 azure。")

        output_txt = audio_path.with_suffix(".txt")

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"\n文字轉換成功！結果已儲存至: {output_txt}")
        print("後續請由 AI Agent 將此文本檔案與音訊一併整理至對應分類目錄下。")

    except Exception as e:
        print(f"\n文字轉換過程中發生錯誤: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
