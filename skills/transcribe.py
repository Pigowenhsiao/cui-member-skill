# /// script
# dependencies = [
#     "python-dotenv",
#     "openai",
#     "mlx-whisper",
#     "faster-whisper",
#     "mutagen",
# ]
# ///
import os
import sys
import argparse
import platform
from dotenv import load_dotenv

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


def format_segments(segments: list) -> str:
    """
    セグメントリストを整形して文字列を返す。
    - 各セグメントは改行で区切る
    - 句点（。！？…）で終わるセグメントの後には空行を追加
    """
    SENTENCE_END = ("。", "！", "？", "…", "!", "?")
    lines = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(text)
        if text.endswith(SENTENCE_END):
            lines.append("")   # 文末後に空行
    return "\n".join(lines)


def print_progress(current_sec: float, total_sec: float, prefix: str = "") -> None:
    """現在の進捗をコンソールに出力する（stderr）。"""
    if total_sec <= 0:
        return
    pct = min(current_sec / total_sec * 100, 100.0)
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    msg = f"\r{prefix}[{bar}] {pct:5.1f}%  ({current_sec:.0f}s / {total_sec:.0f}s)"
    print(msg, end="", flush=True, file=sys.stderr)


# ---------------------------------------------------------------------------
# 転写バックエンド
# ---------------------------------------------------------------------------

def transcribe_local(audio_path: str) -> str:
    is_mac_arm = platform.system() == "Darwin" and platform.machine() == "arm64"
    total_sec = get_audio_duration(audio_path)

    if is_mac_arm:
        print(f"偵測到 Apple Silicon macOS，使用本地 mlx-whisper 進行 GPU 加速語音識別 (音訊: {audio_path})...")
        import mlx_whisper
        model = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-mlx")
        print(f"載入模型: {model}")

        # mlx_whisper は verbose=True のとき segment を stdout に流す。
        # 進捗を自前で取るため verbose=False にし、segments を走査する。
        raw = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=model,
            language="zh",
            verbose=False       # 自前で進捗表示するため False
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

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="zh",
            response_format="verbose_json"  # セグメント情報を取得
        )

    # verbose_json の場合 segments が含まれる
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

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model=deployment,
            file=f,
            language="zh",
            response_format="verbose_json"
        )

    if hasattr(transcript, "segments") and transcript.segments:
        seg_dicts = [{"text": s.text} for s in transcript.segments]
        return format_segments(seg_dicts)
    return transcript.text


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="語音文字稿轉換工具 (支援 Local, OpenAI API, Azure OpenAI)")
    parser.add_argument("audio_file", help="要轉換的音訊檔案路徑 (例如 .mp3)")
    args = parser.parse_args()

    load_dotenv()

    mode = os.getenv("WHISPER_MODE", "local").lower()

    if not os.path.exists(args.audio_file):
        print(f"錯誤: 找不到音訊檔案 {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    try:
        if mode == "local":
            text = transcribe_local(args.audio_file)
        elif mode == "openai":
            text = transcribe_openai(args.audio_file)
        elif mode == "azure":
            text = transcribe_azure(args.audio_file)
        else:
            raise ValueError(f"未知的 WHISPER_MODE: {mode}。請設定為 local, openai 或 azure。")

        # 結果保存
        base_name  = os.path.splitext(args.audio_file)[0]
        output_txt = f"{base_name}.txt"

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"\n文字轉換成功！結果已儲存至: {output_txt}")
        print("後續請由 AI Agent 將此文本檔案與音訊一併整理至對應分類目錄下。")

    except Exception as e:
        print(f"\n文字轉換過程中發生錯誤: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
