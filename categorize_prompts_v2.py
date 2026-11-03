#!/usr/bin/env python3
"""Improved categorization."""
import json, re
from pathlib import Path
from datetime import datetime

with open(Path.home() / "Downloads" / "toggles_raw.json") as f:
    data = json.load(f)

CATEGORIES = {
    "美學海報": {
        "keywords": ["極簡", "大色塊", "彌散", "剪影", "透明介質", "清新治愈", "呼吸感", "減法", "golden elegance", "glow", "清冷油墨"],
        "titles": ["極簡", "大色塊", "海報", "美學"]
    },
    "字體設計": {
        "keywords": ["字體", "漢字", "大字報", "字體氣質", "字體變實體", "字骨", "字體重構"],
        "titles": ["字體", "漢字", "Logo", "logo", "大字報"]
    },
    "電商素材": {
        "keywords": ["電商", "電商廣告", "門店", "淘寶", "義烏", "促單", "畫冊", "餐飲品牌", "餐飲畫冊"],
        "titles": ["電商", "廣告", "寸照", "二維碼", "banner", "Banner"]
    },
    "資訊圖卡": {
        "keywords": ["信息圖", "百科", "知識圖鑑", "進化史", "萬物簡史", "信息海報", "圖鑑", "生物知識", "建筑知识"],
        "titles": ["信息卡", "百科", "圖鑑", "信息圖"]
    },
    "PPT/教學": {
        "keywords": ["課件", "老師", "教學PPT", "語文老師", "生物老師"],
        "titles": ["PPT", "教學", "課件"]
    },
    "創意頭像": {
        "keywords": ["頭像", "情頭", "抽象頭像", "線條頭", "線條融一切"],
        "titles": ["頭像", "情頭", "抽象頭像", "線條頭"]
    },
    "遊戲/趣味": {
        "keywords": ["面相", "狗", "底特律", "手相", "命相"],
        "titles": ["遊戲", "長相", "面相", "狗", "趣味測試", "底特律"]
    },
    "中國風": {
        "keywords": ["生肖", "星座", "二十四節氣", "詩詞", "山海經", "古畫", "文物", "中式", "中國風", "國風", "文化解讀", "成語", "典故", "端午", "春節"],
        "titles": ["中式", "中國風", "山海經", "古畫", "文物", "生肖", "星座", "二十四節氣", "國風"]
    },
    "醫療/健康": {
        "keywords": ["中藥", "植物圖鑑", "生物標本"],
        "titles": ["中藥", "植物圖鑑", "生物"]
    },
    "建築/城市": {
        "keywords": ["建築知識", "微縮", "城市", "日簽", "傍晚黃金"],
        "titles": ["建築", "微縮", "紀念碑谷", "城市", "日簽"]
    },
    "修圖/塗鴉": {
        "keywords": ["廢片", "智能手繪", "凈化", "變萌", "自動修圖", "塗鴉"],
        "titles": ["修圖", "塗鴉", "廢片", "凈化"]
    },
    "攝影/寫實": {
        "keywords": ["真實質感", "抓拍", "紀錄片", "氛圍", "三分構圖", "黃金時間"],
        "titles": ["寫實", "攝影", "紀錄片", "抓拍", "光影"]
    },
    "商務/品牌": {
        "keywords": ["商務", "科技風", "品牌", "高端餐飲"],
        "titles": ["商務", "科技風", "品牌"]
    },
    "社媒運營": {
        "keywords": ["小紅書", "自媒體", "封面", "小红书"],
        "titles": ["小紅書", "自媒體", "封面", "小红书"]
    },
    "創意玩法": {
        "keywords": ["漫畫", "日語變漫畫", "圖片變漫畫", "日漫", "樂高", "元器件", "電子元器件", "拼貼", "碎紙風", "創意玩法"],
        "titles": ["漫畫", "日記變漫畫", "圖片變漫畫", "樂高", "創意玩法"]
    },
    "提示詞技巧": {
        "keywords": ["使用技巧", "佐料", "提示詞技巧", "聰明人", "記憶遊戲"],
        "titles": ["使用技巧", "提示詞技巧", "技巧"]
    },
    "實戰技巧": {
        "keywords": ["實戰", "實例", "案例"],
        "titles": ["實戰", "實例"]
    },
}

def categorize(title, content):
    tl = title.lower()
    cl = content[:800].lower()
    for cat, rules in CATEGORIES.items():
        for kw in rules.get("keywords", []):
            if kw.lower() in tl or kw.lower() in cl:
                return cat
    # Second pass - title only
    for cat, rules in CATEGORIES.items():
        for kw in rules.get("titles", []):
            if kw in title:
                return cat
    return "其他"

categorized = {}
for item in data:
    cat = categorize(item["title"], item["content"])
    if cat not in categorized:
        categorized[cat] = []
    categorized[cat].append(item)

# Sort each category by title
for cat in categorized:
    categorized[cat].sort(key=lambda x: x["title"])

print("Categories:")
for cat, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
    print(f"  {cat}: {len(items)}")

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
    safe_cat = cat.replace("/", "-").replace(" ", "")
    out_path = OUTPUT_DIR / f"小小東Prompt_{safe_cat}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(body)

print(f"\n{len(categorized)} files written to {OUTPUT_DIR}")
