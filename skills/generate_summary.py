# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "python-dotenv",
#     "openai",
# ]
# ///
"""
自動生成 summary.md 摘要腳本
支援 OpenAI API / Azure OpenAI / 本地模型（未來擴展）

用法：
  SUMMARY_MODE=openai   uv run python skills/generate_summary.py <audio.txt> <info.json> <分類> <輸出目錄>
  SUMMARY_MODE=azure   uv run python skills/generate_summary.py ...
"""
import os
import sys
import json
import re
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ─── Prompt 模板 ──────────────────────────────────────────────────────────

SUMMARY_PROMPT = """你是小翠時政財經的內容整理專家。以下是某支影片的逐字稿，請生成結構化的摘要。

## 影片資訊
- 頻道：{channel}
- 影片標題：{title}
- 影片 ID：{video_id}
- 影片 URL：https://www.youtube.com/watch?v={video_id}
- 分類：{category}
- 摘要生成時間：{generate_date}

## 逐字稿內容
{audio_text}

## 輸出格式要求

請嚴格依照以下格式輸出，不要遺漏任何一個區塊：

# 【{category}】{title}

## 基本資訊

| 欄位 | 內容 |
|------|------|
| **頻道** | {channel} |
| **日期** | {upload_date_display}（美東） |
| **時長** | 約 {duration_min} 分鐘 |
| **分類** | {category} |
| **影片 ID** | {video_id} |
| **主持人觀點** | （從內容推斷主持人立場） |

---

## {section_1_title}

### {section_1_1_title}
- （重點 1）
- （重點 2）

### {section_1_2_title}
- （重點 1）
- （重點 2）

---

## {section_2_title}

### {section_2_1_title}
- （重點 1）
- （重點 2）

---

## 重點個股（如有）

| 公司 | 重點 |
|------|------|
| **公司名** | （描述） |

---

## 術語勘誤對照

| Whisper 誤識別 | 正確用詞 |
|---------------|---------|
| （錯字） | （正確） |

---

## Source

- 影片：[{title}](https://www.youtube.com/watch?v={video_id})
- 文字稿：{rel_txt_path}
- Metadata：{rel_info_path}
- 摘要生成：{model_info}
- 摘要日期：{generate_date}

---

## 注意事項
1. 如果逐字稿中出現明顯的 Whisper 識別錯誤，請在「術語勘誤對照」表中列出
2. 「主持人觀點」欄位請從內容語氣推斷，不要捏造
3. 若影片涉及多個主題，請相應增加章節
4. 數據（日期、數字、百分比）請盡量準確
5. 尚未確認的內容請標記「（待確認）」
"""


def build_prompt(audio_text: str, video_info: dict, category: str) -> str:
    title = video_info.get("title", "未知標題")
    video_id = video_info.get("id", "")
    channel = video_info.get("uploader", "小翠時政財經")
    upload_date = video_info.get("upload_date", "")
    duration = video_info.get("duration", 0)
    duration_min = max(1, round(duration / 60)) if duration else "未知"

    upload_date_display = (
        f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        if len(upload_date) == 8
        else upload_date
    )

    # 偵測主要內容主題
    text_lower = audio_text.lower()
    topics = []
    if any(w in text_lower for w in ["伊朗", "制裁", "核"]): topics.append("伊朗局勢")
    if any(w in text_lower for w in ["川普", "關稅", "無人機"]): topics.append("川普政策")
    if any(w in text_lower for w in ["資金", "流入", "美銀", "黃金"]): topics.append("資金流向")
    if any(w in text_lower for w in ["經濟", "PPI", "CPI", "就業"]): topics.append("總體經濟")
    if any(w in text_lower for w in ["記憶體", "半導體", "芯片"]): topics.append("記憶體與半導體")
    if any(w in text_lower for w in ["機器人", "人形"]): topics.append("機器人")
    if any(w in text_lower for w in ["輝達", "英偉達", "NVIDIA", "AMD"]): topics.append("晶片與個股")
    if any(w in text_lower for w in ["京東", "阿里巴巴", "中國", "A股"]): topics.append("中國經濟")
    if any(w in text_lower for w in ["OpenAI", "ChatGPT", "GPT"]): topics.append("AI 動態")
    if any(w in text_lower for w in ["軟體", "軟件", "軟體"]): topics.append("軟體")
    if not topics:
        topics = ["主題"]

    # 建立章節標題
    section_1_title = topics[0] if len(topics) > 0 else "主要內容"
    section_1_1_title = f"{section_1_title}（一）"
    section_1_2_title = f"{section_1_title}（二）"
    section_2_title = topics[1] if len(topics) > 1 else "其他重點"
    section_2_1_title = f"{section_2_title}（一）"
    rel_txt = "audio.txt"
    rel_info = "audio.info.json"

    model_info = f"{os.getenv('SUMMARY_MODE', 'openai').upper()}（generate_summary.py）"

    if len(audio_text) > 8000:
        print(f"[WARN] 逐字稿 {len(audio_text)} 字已截斷至 8000 字（避免 token 超出）", file=sys.stderr)
    return SUMMARY_PROMPT.format(
        channel=channel,
        title=title,
        video_id=video_id,
        category=category,
        upload_date_display=upload_date_display,
        duration_min=duration_min,
        audio_text=audio_text[:8000],
        section_1_title=section_1_title,
        section_1_1_title=section_1_1_title,
        section_1_2_title=section_1_2_title,
        section_2_title=section_2_title,
        section_2_1_title=section_2_1_title,
        generate_date=datetime.now().strftime("%Y-%m-%d"),
        model_info=model_info,
        rel_txt_path=rel_txt,
        rel_info_path=rel_info,
    )


def call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("未設定 OPENAI_API_KEY 環境變數")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_azure(prompt: str) -> str:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_minimax(prompt: str) -> str:
    import urllib.request
    import urllib.error
    api_key = os.getenv("MINIMAX_API_KEY")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
    if not api_key:
        raise ValueError("未設定 MINIMAX_API_KEY 環境變數")

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.minimax.io/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def generate_summary(audio_path: str, info_path: str, category: str, out_dir: str) -> str:
    # 讀取音頻文字稿
    with open(audio_path, "r", encoding="utf-8") as f:
        audio_text = f.read()

    # 讀取 metadata
    with open(info_path, "r", encoding="utf-8") as f:
        video_info = json.load(f)

    video_id = video_info.get("id", "")
    title = video_info.get("title", "未知標題")
    # 淨化標題作為檔名
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:50]

    # 建立 prompt
    prompt = build_prompt(audio_text, video_info, category)

    # 依模式呼叫 LLM
    mode = os.getenv("SUMMARY_MODE", "openai").lower()
    if mode == "openai":
        summary_text = call_openai(prompt)
    elif mode == "azure":
        summary_text = call_azure(prompt)
    elif mode == "minimax":
        summary_text = call_minimax(prompt)
    else:
        raise ValueError(f"不支援的 SUMMARY_MODE：{mode}")

    # 修正 prompt 中的預留位置
    base_name = f"{safe_title} [{video_id}]"
    rel_txt = f"docs/{category}/{video_id[:8]}/{base_name}.txt"
    rel_info = f"docs/{category}/{video_id[:8]}/{base_name}.info.json"
    summary_text = summary_text.replace("{rel_txt_path}", rel_txt)
    summary_text = summary_text.replace("{rel_info_path}", rel_info)

    # 寫入 summary.md
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "summary.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    return out_path


def main():
    parser = argparse.ArgumentParser(description="自動生成 summary.md 摘要")
    parser.add_argument("audio_file", help="文字稿檔案（.txt）")
    parser.add_argument("info_file", help="影片 metadata（.info.json）")
    parser.add_argument("category", help="分類（如：每日要聞、會員直播、AI技術教學）")
    parser.add_argument("output_dir", help="輸出目錄")
    args = parser.parse_args()

    if not os.path.exists(args.audio_file):
        print(f"錯誤：找不到文字稿 {args.audio_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.info_file):
        print(f"錯誤：找不到 metadata {args.info_file}", file=sys.stderr)
        sys.exit(1)

    try:
        out_path = generate_summary(
            args.audio_file,
            args.info_file,
            args.category,
            args.output_dir,
        )
        print(f"\n摘要生成完成：{out_path}")
    except Exception as e:
        print(f"錯誤：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
