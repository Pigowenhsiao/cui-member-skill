# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
#     "mutagen",
# ]
# ///
"""
Whisper GPU 轉譯腳本
使用系統 Anaconda 環境的 openai-whisper（GPU 版本）
路徑: D:\\anaconda3\\python.exe + openai-whisper
"""
import os, sys, platform, argparse
from dotenv import load_dotenv

# ─── Anaconda Python 路徑 ────────────────────────────────────────────────
ANACONDA_PYTHON = r"D:\anaconda3\python.exe"

def format_segments(segments):
    """格式化時間戳段落為連續文字"""
    SENTENCE_END = ("。", "！", "？", "…", "!", "?")
    lines = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(text)
        if text.endswith(SENTENCE_END):
            lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Whisper GPU 轉譯（使用 Anaconda openai-whisper）")
    parser.add_argument("audio_file", help="音訊檔案路徑 (.mp3, .wav, ...)")
    parser.add_argument("--model", default="small", help="Whisper 模型 (default: small)")
    parser.add_argument("--language", default="zh", help="語言代碼 (default: zh)")
    args = parser.parse_args()
    load_dotenv()

    audio_path = args.audio_file
    if not os.path.exists(audio_path):
        print(f"錯誤: 找不到音訊檔案 {audio_path}", file=sys.stderr)
        sys.exit(1)

    output_txt = os.path.splitext(audio_path)[0] + ".txt"

    # ── 透過子進程呼叫 Anaconda Python + whisper API ──────────────────
    code = f'''
import whisper
import sys

model = whisper.load_model("{args.model}", device="cuda")
print("Model loaded on GPU", file=sys.stderr)

result = model.transcribe("{audio_path}", language="{args.language}")
print(f"Transcription done: {{len(result['text'])}} chars", file=sys.stderr)

with open(r"{output_txt}", "w", encoding="utf-8") as f:
    f.write(result["text"])

print("Done!", file=sys.stderr)
'''

    import subprocess
    print("🚀 使用 NVIDIA GPU + CUDA 加速轉譯...", file=sys.stderr)
    result = subprocess.run(
        [ANACONDA_PYTHON, "-c", code],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        print(f"錯誤: Whisper 轉譯失敗 (exit {result.returncode})", file=sys.stderr)
        if result.stdout:
            print(result.stdout[:500], file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ 轉譯完成！結果已儲存至: {output_txt}", file=sys.stderr)

if __name__ == "__main__":
    main()
