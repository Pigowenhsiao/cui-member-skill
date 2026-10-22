# /// script
# dependencies = [
#     "requests",
#     "python-dotenv",
#     "beautifulsoup4",
# ]
# ///
"""
台股財報分析 Workflow 入口腳本

用法：
  uv run skills/tw_stock_analysis.py "2330"
  uv run skills/tw_stock_analysis.py "台積電"
  uv run skills/tw_stock_analysis.py "聯發科"

功能：
  1. 解析台股代碼
  2. 搜尋最近四季財報資料（月營收、季報、新聞）
  3. 將蒐集結果寫入 docs/股票分析/<代碼>_<日期>/research.md
  4. 輸出引導提示，交由 AI Agent 完成完整分析

實際分析（閱讀財報、給出投資觀點）由 AI Agent 根據 research.md 內容完成。
"""

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────
# 1. 台股代碼對照表
# ─────────────────────────────────────────
TWSE_TICKERS = {
    "台積電": "2330",
    "聯發科": "2454",
    "聯發科": "2454",
    "中華電": "2412",
    "聯電": "2303",
    "鴻海": "2317",
    "富邦金": "2881",
    "國泰金": "2882",
    "中信金": "2891",
    "台達電": "2308",
    "華碩": "2357",
    "宏碁": "2353",
    "廣達": "2382",
    "仁寶": "2324",
    "緯創": "3231",
    "友達": "2409",
    "群創": "3481",
    "聯強": "2347",
    "景碩": "3189",
    "全新": "2455",
    "宏捷科": "8086",
    "穩懋": "3105",
    "精材": "3374",
    "台郡": "6269",
    "欣興": "3037",
    "南電": "8054",
    "日月光投控": "3711",
    "日月光": "3711",
    "力成": "6239",
    "世界先進": "5347",
    "杰力": "5299",
    "和大": "1536",
    "江申": "1525",
    "IKTA": "2480",
    "吉祥全": "2491",
    "TPK": "3673",
    "洋華": "3624",
    "景碩": "3189",
    "光耀": "3662",
    "同欣電": "6271",
    "先豐": "5347",
    "安馳": "3662",
    "合庫金": "5880",
    "兆豐金": "2886",
    "玉山金": "2884",
    "華南金": "2880",
    "開發金": "2883",
    "新光金": "2888",
    "元大金": "2885",
    "永豐金": "2890",
    "台灣大": "3045",
    "遠傳": "4904",
    "中華車": "2204",
    "裕隆": "2201",
    "和泰": "2207",
    "為": "2206",
    "光陽": "2236",
    "三陽": "2204",
    "敬德": "3028",
    "必較": "3047",
    "新普": "6121",
    "順達": "3211",
    "新世紀": "3380",
    "統振": "6170",
    "德微": "3675",
    "朋程": "8255",
    "奇力新": "2456",
    "大毅": "2478",
    "聚鼎": "6224",
    "晶技": "3042",
    "加高": "3312",
    "希華": "2484",
    "元山": "3045",
    "健鼎": "3044",
    "敬得": "3026",
    "台光電": "2383",
    "聯茂": "6213",
    "台燿": "6274",
    "騰輝": "6274",
    "日電": "2374",
    "友訊": "2332",
    "合勤": "3708",
    "中磊": "5388",
    "正文": "3499",
    "智易": "3596",
    "啟碁": "3164",
    "明泰": "3380",
    "仲琦": "3708",
    "升達": "3499",
    "康全": "3580",
    "訊舟": "3047",
    "海華": "3694",
    "正文": "3499",
    "華冠": "8101",
    "華冠通": "8103",
    "華冠": "8101",
    "凱碩": "3413",
    "百一": "6152",
    "振榕": "3211",
    "光鼎": "6226",
    "今國光": "6209",
    "玉晶": "3406",
    "新鉅科": "3630",
    "先進光": "3615",
    "聯一": "3051",
    "聯光": "3051",
    "程瑞": "3579",
    "秀育": "6737",
    "佳萊": "1258",
    "迎廣": "6117",
    "建準": "2421",
    "奇鋐": "3017",
    "力致": "3483",
    "雙鴻": "3324",
    "晟琦": "3630",
    "健策": "3653",
    "立訊": "6528",
    "詠昇": "3189",
    "胡連": "6279",
    "信昌電": "6173",
    "佳邦": "6158",
    "禾伸堂": "3026",
    "強茂": "2481",
    "德微": "3675",
    "虹冠電": "6514",
    "力智": "6719",
    "通嘉": "3588",
    "致新": "8081",
    "類比科": "3438",
    "茂達": "6138",
    "尼克": "6064",
    "晶焱": "6416",
    "聚積": "3567",
    "M31": "6443",
    "力旺": "3529",
    "嵌軟": "6480",
    "世芯": "3661",
    "創意": "3443",
    "愛普": "6531",
    "VHQ": "4803",
    "華研": "8446",
    "昇佳": "6732",
    "邑錡": "3105",
    "久元": "6261",
    "天虹": "8086",
    "中美晶": "5483",
    "綠能": "3519",
    "陽程": "3498",
    "可成": "2474",
    "TPK": "3673",
    "洋華": "3624",
    "富軌": "1526",
    "IKTA": "2480",
    "吉祥全": "2491",
    "百達": "3376",
    "宜特": "3443",
    "閎康": "3587",
    "光罩": "2338",
    "辛耘": "3563",
    "帆宣": "6196",
    "聖暉": "5536",
    "漢唐": "2404",
    "洋基": "6612",
    "中工": "2511",
    "ER": "2511",
    "根基": "5506",
    "華建": "2530",
    "宏璟": "2527",
    "達麗": "6177",
    "志嘉": "6329",
    "聯上": "6137",
    "順天": "5515",
    "鄉林": "5531",
    "太子": "2512",
    "華固": "2548",
    "長虹": "5521",
    "潤弘": "2597",
    "新建": "5536",
    "冠德": "2520",
    "興富發": "2542",
    "皇翔": "2545",
    "遠雄": "5522",
    "華固": "2548",
    "聯上": "6137",
    "日勝生": "2577",
    "三發": "2546",
    "全坤": "2509",
    "達麗": "6177",
    "坤悅": "1456",
    "綠意": "2590",
    "京城": "4109",
    "隆大": "5519",
    "聯上": "6137",
    "合庫": "5880",
    "永豐": "2890",
    "一卡通": "6167",
    "遠雄": "5522",
    "中工": "2511",
    "根基": "5506",
    "新建": "5536",
    "冠德": "2520",
    "興富發": "2542",
    "皇翔": "2545",
    "華固": "2548",
    "長虹": "5521",
    "潤弘": "2597",
    "鄉林": "5531",
    "全坤": "2509",
    "達麗": "6177",
    "坤悅": "1456",
    "京城": "4109",
    "隆大": "5519",
    "宏璟": "2527",
    "華建": "2530",
    "志嘉": "6329",
    "順天": "5515",
    "日勝生": "2577",
    "太子": "2512",
    "三發": "2546",
    "中工": "2511",
    "富軌": "1526",
    "根基": "5506",
    "新建": "5536",
    "冠德": "2520",
    "興富發": "2542",
    "皇翔": "2545",
    "華固": "2548",
    "長虹": "5521",
    "潤弘": "2597",
    "鄉林": "5531",
    "達麗": "6177",
    "坤悅": "1456",
    "京城": "4109",
    "隆大": "5519",
    "聯上": "6137",
    "合庫": "5880",
    "永豐": "2890",
    "遠雄": "5522",
    "ER": "2511",
}

# ─────────────────────────────────────────
# 2. 解析代碼
# ─────────────────────────────────────────
def resolve_ticker(raw: str) -> tuple[str, str]:
    """回傳 (ticker_4digit, company_name)"""
    raw = raw.strip()
    # 已是數字代碼
    if re.fullmatch(r"\d{4,6}", raw):
        code = raw.zfill(4)
        name = raw  # 未知名稱，回傳代碼
        return code, name
    # 查對照表
    if raw in TWSE_TICKERS:
        return TWSE_TICKERS[raw], raw
    lower = raw.lower()
    for k, v in TWSE_TICKERS.items():
        if k.lower() == lower:
            return v, k
    # 未知 → 直接用原字當名稱
    return raw, raw


# ─────────────────────────────────────────
# 3. 搜尋函式
# ─────────────────────────────────────────
def web_search(query: str, num_results: int = 8) -> list[dict]:
    """使用 mcporter exa 搜尋"""
    try:
        import subprocess, json
        cmd = [
            "mcporter", "call",
            f'exa.web_search_exa(query: "{query}", numResults: {num_results})'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                items = data if isinstance(data, list) else data.get("results", [])
                return [
                    {"title": it.get("title", ""), "url": it.get("url", ""), "snippet": it.get("snippet", it.get("text", ""))}
                    for it in items
                ]
            except (json.JSONDecodeError, ValueError):
                pass
    except Exception:
        pass
    return []


def search_twse_financials(code: str, name: str) -> dict:
    """搜尋台股財報相關資料"""
    queries = [
        # 月營收
        (f'{name} {code} 2026 月營收 累計營收', "monthly-revenue"),
        (f'{name} {code} 2026年 每月營收 年增率', "monthly-revenue-yoy"),
        # 季報
        (f'{name} {code} 2026 上半年 財報 營收 獲利', "h1-2026"),
        (f'{name} {code} 2026 Q3 營收 季報', "q3-2026"),
        (f'{name} {code} 2026 Q2 財報 季報', "q2-2026"),
        # 年度財報
        (f'{name} {code} 2025 年報 EPS 每股盈餘', "annual-2025"),
        (f'{name} {code} 2025 全年 營收 毛利 淨利', "annual-2025-financial"),
        # 新聞
        (f'{name} {code} 2026 最新 營收 財測', "news-latest"),
        (f'{name} {code} 法說會 2026 營運展望', "investor-conf"),
        (f'{name} {code} 2026 法人說明會 營收指引', "guidance"),
    ]

    results = {}
    for query, label in queries:
        hits = web_search(query, num_results=5)
        results[label] = hits
        status = f"✅ {len(hits)} 筆" if hits else "⚠️ 無結果"
        print(f"  [{label}] {status}")

    return results


# ─────────────────────────────────────────
# 4. 寫出 research.md
# ─────────────────────────────────────────
def write_research(code: str, name: str, search_results: dict) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    out_dir = Path("docs") / "股票分析" / f"TW_{code}_{date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "research.md"

    lines = [
        f"# {name}（{code}）台股財報資料彙整",
        f"> 自動蒐集日期：{datetime.now().strftime('%Y-%m-%d')}｜使用工具：tw_stock_analysis.py｜請 AI Agent 閱讀後完成分析報告",
        "",
        "---",
        "",
        "## 資料讀取優先順序（台股版）",
        "",
        "| 優先順序 | 來源 | 說明 |",
        "|---------|------|------|",
        "| 1 | [公開資訊觀測站](https://mops.twse.com.tw) | 官方財報，含完整營收、損益、資產負債 |",
        "| 2 | [Goodinfo](https://goodinfo.com) | 台股個頁面，含歷史財報、股利、分項營收 |",
        "| 3 | [MoneyDJ](https://moneydj.com) | 財報、新聞、產業分析 |",
        "| 4 | [Yahoo 奇摩股市](https://tw.stock.yahoo.com) | 快速取得日成交資料 |",
        "| 5 | [台灣證券交易所](https://www.twse.com.tw) | 月營收、每日行情 |",
        "",
        "---",
        "",
    ]

    for label, hits in search_results.items():
        lines.append(f"## 【{label}】")
        lines.append("")
        if not hits:
            lines.append("*（未找到相關結果）*")
        for i, hit in enumerate(hits, 1):
            title = hit.get("title", "").strip()
            url = hit.get("url", "").strip()
            snippet = hit.get("snippet", "").strip()
            lines.append(f"### {i}. {title}")
            if url:
                lines.append(f"- URL：{url}")
            lines.append(f"- 摘要：{snippet[:300]}{'...' if len(snippet) > 300 else ''}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines += [
        "## 備註",
        "",
        "以上為自動搜尋結果，請 AI Agent：",
        "1. 點擊相關連結，讀取完整財報內容",
        "2. 提取關鍵財務數據（營收、EPS、毛利率、指引等）",
        "3. 依據 `skills/prompts/tw_stock_analysis_workflow.md` 中的框架完成分析報告",
        "4. 將最終報告儲存為 `analysis.md`",
        "",
        f"分析完成後，請將 `analysis.md` 的路徑回報給使用者。",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ research.md 已寫入：{out_path}")
    return out_path


# ─────────────────────────────────────────
# 5. 主程式
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="台股財報分析 Workflow 入口")
    parser.add_argument("stock", nargs="+", help="台股代碼（4-6位數字）或名稱")
    args = parser.parse_args()

    raw_input = " ".join(args.stock)
    code, name = resolve_ticker(raw_input)

    print(f"\n{'='*50}")
    print(f"台股財報分析 Workflow")
    print(f"{'='*50}")
    print(f"輸入：{raw_input}")
    print(f"識別代碼：{code}")
    print(f"公司名稱：{name}")
    print()

    print("🔍 搜尋台股財報資料...")
    results = search_twse_financials(code, name)

    print("\n📝 寫出 research.md...")
    research_path = write_research(code, name, results)

    print()
    print("=" * 50)
    print("✅ 資料蒐集完成！")
    print()
    print("請 AI Agent 依據以下步驟完成分析：")
    print(f"  1. 閱讀 {research_path}")
    print("  2. 點擊相關連結，讀取完整財報（優先：公開資訊觀測站、Goodinfo）")
    print("  3. 依據 `skills/prompts/tw_stock_analysis_workflow.md` 框架完成分析")
    print(f"  4. 將報告儲存為 `docs/股票分析/TW_{code}_*/analysis.md`")
    print()
    print("或直接執行 `/analyze_twstock {code}` 交由 AI Agent 完成完整分析。")
    print("=" * 50)


if __name__ == "__main__":
    main()
