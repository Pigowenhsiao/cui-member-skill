# /// script
# requires-python = ">=3.10"
# ///
"""
字幕勘誤腳本：從 Whisper / YouTube 字幕中偵測並修正常見錯誤

用法：
  uv run python skills/correct_transcript.py <audio.txt> [--output <output.txt>] [--json]

Whisper 常見錯誤模式：
  - 數字唸錯（衰/摔、衰退聽成摔腿）
  - 人名混淆（蘇姿丰→蘇媽、赫格塞斯→赫格賽斯）
  - 術語漏譯（Recession→衰退、GDP→常規術語）
"""
import os
import sys
import json
import re
import argparse

# ─── 勘誤規則 ───────────────────────────────────────────────────────────

# 常見 Whisper 誤識別（錯字 → 正確）
WHISPER_ERRORS = [
    ("衰退", "摔腿"),
    ("赫格塞斯", "赫格賽斯"),
    ("萊特", "萊特斯"),
    ("貝森特", "貝森"),
    ("黃金", "蝗金"),
    ("輝達", "灰達"),
    ("華許（Kevin Warsh）", "沃什"),
    ("摩根士丹利", "摩根斯坦利"),
    ("蘇姿丰", "蘇媽"),
    # 崔泰源：罕見人名，正則已處理；此列為 no-op 保留供人工確認
    ("人形機器人", "人型機器人"),
    ("芯片", "晶片"),
]

# 術語正則比對（正則模式 → 替換為）
TERM_PATTERNS = [
    # 公司/人名
    (r"蘇媽", "蘇姿丰（Lisa Su）"),
    (r"皮柴", "皮查伊（Sundar Pichai）"),
    (r"阿爾特曼", "阿特曼（Sam Altman）"),
    (r"崔泰源(?![（　])", "崔泰源（SK 海力士董事長）"),
    (r"赫格塞斯", "赫格塞斯（Hegseth，美國國防部長）"),
    (r"萊特(?![　\(])", "萊特（Wright，能源部長）"),
    (r"貝森特(?![（　])", "貝森特（Bessent，財政部長）"),
    (r"萬斯", "萬斯（Vance，美國副總統）"),
    # 英文縮寫
    (r"\bAI\b", "AI（人工智慧）"),
    (r"\bGDP\b", "GDP（國內生產總值）"),
    (r"\bPPI\b", "PPI（生產者物價指數）"),
    (r"\bCPI\b", "CPI（消費者物價指數）"),
    (r"\bETF\b", "ETF（交易所交易基金）"),
    (r"\bHBM\b", "HBM（高效能記憶體）"),
    (r"\bH100\b", "H100（NVIDIA GPU）"),
    (r"\bGB200\b", "GB200（NVIDIA GPU）"),
    (r"\bGB300\b", "GB300（NVIDIA GPU）"),
    (r"\bCPO\b", "CPO（共同封裝光學）"),
    (r"\bSOP\b", "SOP（標準作業程序）"),
    (r"\bVRAM\b", "VRAM（顯示記憶體）"),
    (r"\bUSD\b", "USD（美元）"),
    (r"\bRMB\b", "RMB（人民幣）"),
    # 全形數字 → 半形（常見於 YouTube 自動字幕）
    (r"１", "1"), (r"２", "2"), (r"３", "3"),
    (r"４", "4"), (r"５", "5"), (r"６", "6"),
    (r"７", "7"), (r"８", "8"), (r"９", "9"),
    (r"０", "0"),
]


def correct_text(text: str) -> tuple[str, list[dict]]:
    """
    對文字稿進行勘誤。
    傳回 (勘誤後文字, 錯誤記錄列表)
    """
    corrections = []
    corrected = text

    # 簡單字串替換
    for true_val, error_val in WHISPER_ERRORS:
        if error_val in corrected:
            corrected = corrected.replace(error_val, true_val)
            corrections.append({
                "error": error_val,
                "corrected": true_val,
                "type": "whisper_error",
            })

    # 正則比對
    for pattern, replacement in TERM_PATTERNS:
        new_text = re.sub(pattern, replacement, corrected)
        if new_text != corrected:
            corrections.append({
                "pattern": pattern,
                "replaced_with": replacement,
                "type": "terminology",
            })
            corrected = new_text

    return corrected, corrections


def main():
    parser = argparse.ArgumentParser(description="字幕勘誤腳本")
    parser.add_argument("input_file", help="要勘誤的文字稿（.txt）")
    parser.add_argument("--output", "-o", help="輸出檔案路徑（預設：覆寫原檔）")
    parser.add_argument("--json", action="store_true", help="同時輸出勘誤記錄 JSON")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"錯誤：找不到檔案 {args.input_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r", encoding="utf-8") as f:
        original = f.read()

    corrected_text, corrections = correct_text(original)

    output_path = args.output or args.input_file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(corrected_text)

    print(f"勘誤完成：{len(corrections)} 處修正 → {output_path}")

    if args.json or corrections:
        json_path = output_path.replace(".txt", "_corrections.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "source": args.input_file,
                "total_corrections": len(corrections),
                "corrections": corrections,
            }, f, ensure_ascii=False, indent=2)
        print(f"勘誤記錄：{json_path}")

    if not corrections:
        print("（無需修正）")


if __name__ == "__main__":
    main()
