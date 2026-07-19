# /// script
# dependencies = [
#     "python-dotenv",
#     "openai",
#     "mlx-whisper",
#     "faster-whisper",
# ]
# ///
import os
import sys
import argparse
import platform
from dotenv import load_dotenv

def transcribe_local(audio_path):
    # 偵測是否為 Apple Silicon macOS
    is_mac_arm = platform.system() == "Darwin" and platform.machine() == "arm64"
    
    if is_mac_arm:
        print(f"偵測到 Apple Silicon macOS，使用本地 mlx-whisper 進行 GPU 加速語音識別 (音訊: {audio_path})...")
        import mlx_whisper
        model = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-mlx")
        print(f"載入模型: {model}")
        
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=model,
            language="zh",
            verbose=True
        )
        return result["text"]
    else:
        print(f"非 Apple Silicon 環境，使用 CPU 版 faster-whisper (型號: medium) 進行語音識別 (音訊: {audio_path})...")
        from faster_whisper import WhisperModel
        
        # CPU 執行，使用 int8 量化減少記憶體並加速
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        
        segments, info = model.transcribe(audio_path, beam_size=5, language="zh")
        print(f"偵測語言為 '{info.language}'，信心度 {info.language_probability:.2f}")
        
        text_list = []
        for segment in segments:
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            text_list.append(segment.text)
            
        return "".join(text_list)

def transcribe_openai(audio_path):
    print(f"使用 OpenAI API 進行語音識別 (音訊: {audio_path})...")
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("未設定 OPENAI_API_KEY 環境變數。")
    
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="zh"
        )
    return transcript.text

def transcribe_azure(audio_path):
    print(f"使用 Azure OpenAI API 進行語音識別 (音訊: {audio_path})...")
    from openai import AzureOpenAI
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not all([api_key, endpoint, deployment_name]):
        raise ValueError("請檢查 Azure 相關環境變數 (API_KEY, ENDPOINT, DEPLOYMENT_NAME) 是否設定完整。")
    
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )
    
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model=deployment_name,
            file=f,
            language="zh"
        )
    return transcript.text

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
        
        # 儲存結果
        base_name = os.path.splitext(args.audio_file)[0]
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
