#!/usr/bin/env python3
"""Categorize prompts and output markdown files."""
import json, re
from pathlib import Path
from datetime import datetime

with open(Path.home() / "Downloads" / "toggles_raw.json") as f:
    data = json.load(f)

CATEGORIES = {
    "美學海報": ["極簡", "極簡風", "大色塊", "彌散", "剪影", "透明介質", "清新治愈", "極簡", "減法", "呼吸感"],
    "字體設計": ["字體", "漢字", "Logo", "logo", "大字報", "字體藝術", "字體氣質", "字體美學", "字體變實體", "漢字重新設計"],
    "電商素材": ["電商", "Banner", "banner", "廣告圖", "廣告", "寸照", "二維碼", "淘寶", "义乌"],
    "資訊圖卡": ["信息卡", "百科", "知識圖鑑", "圖鑑", "進化史", "萬物簡史", "信息海報", "教學卡"],
    "PPT/教學": ["PPT", "海報", "教學", "課件", "老師"],
    "創意頭像": ["頭像", "情頭", "抽象頭像", "線條頭", "線條頭像", "抽象", "線條融一切"],
    "遊戲/趣味": ["遊戲", "長相", "面相", "狗", "趣味", "測試", "底特律"],
    "中國風": ["中式", "中國風", "山海經", "詩詞", "古畫", "文物", "生肖", "星座", "二十四節氣", "國風", "文化"],
    "醫療/健康": ["中藥", "植物圖鑑", "生物", "圖鑑"],
    "建築/城市": ["建築", "微縮", "紀念碑谷", "城市", "日簽", "風景"],
    "修圖/塗鴉": ["修圖", "塗鴉", "廢片", "智能手繪", "凈化", "變萌"],
    "攝影/寫實": ["寫實", "真實質感", "抓拍", "紀錄片", "氛圍", "光影"],
    "容器/創意": ["Container", "容器", "logo設計", "設計師"],
    "商務/科技": ["商務", "科技風", "启示录"],
    "PPT工具": ["HTML方案", "網頁方案"],
}

def categorize(title, content):
    title_lower = title.lower()
    content_lower = content[:500].lower()  # First 500 chars of content
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in title_lower or kw.lower() in content_lower:
                return cat
    # Fallback by title keywords
    if "PPT" in title or "海報" in title:
        return "PPT/教學"
    if "頭像" in title or "抽象" in title:
        return "創意頭像"
    if "設計" in title or "美學" in title:
        return "美學海報"
    if "提示詞" in title and "技巧" in title:
        return "提示詞技巧"
    return "其他"

# Assign categories
categorized = {}
for item in data:
    cat = categorize(item["title"], item["content"])
    if cat not in categorized:
        categorized[cat] = []
    categorized[cat].append(item)

print("Categories:")
for cat, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
    print(f"  {cat}: {len(items)}")

# Output markdown files
OUTPUT_DIR = Path.home() / "Downloads"
today = datetime.now().strftime("%Y-%m-%d")

for cat, items in categorized.items():
    lines = [
        "# 小小東Prompt",
        f"## {cat}",
        "",
        f"來源：[小小東Prompt](https://x.com/xiaoxiaodong01) | 整理日期：{today}",
        f"共 {len(items)} 筆",
        "",
        "---",
        ""
    ]
    for item in items:
        lines.append(f"### {item['title']}")
        lines.append("")
        lines.append("```")
        lines.append(item["content"])
        lines.append("```")
        lines.append("")
    body = "\n".join(lines)
    safe_cat = cat.replace("/", "-")
    out_path = OUTPUT_DIR / f"小小東Prompt_{safe_cat}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Written: {out_path.name}")

# Also write full merged file
all_lines = [
    "# 小小東Prompt 完整版",
    "",
    f"來源：[小小東Prompt](https://x.com/xiaoxiaodong01) | 整理日期：{today}",
    f"共 {len(data)} 筆，分 {len(categorized)} 個類別",
    "",
    "---",
    ""
]
for cat, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
    all_lines.append(f"## {cat}（{len(items)} 筆）")
    all_lines.append("")
    for item in items:
        all_lines.append(f"### {item['title']}")
        all_lines.append("")
        all_lines.append("```")
        all_lines.append(item["content"])
        all_lines.append("```")
        all_lines.append("")
    all_lines.append("---")
    all_lines.append("")

with open(OUTPUT_DIR / "小小東Prompt_全部.md", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines))
print(f"\nWritten: 小小東Prompt_全部.md")
