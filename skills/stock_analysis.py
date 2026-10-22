# /// script
# dependencies = [
#     "requests",
#     "python-dotenv",
#     "beautifulsoup4",
# ]
# ///
"""
股票財報分析 Workflow 入口腳本

用法：
  uv run skills/stock_analysis.py "NVDA"
  uv run skills/stock_analysis.py "輝達"
  uv run skills/stock_analysis.py "Palantir" "PLTR"

功能：
  1. 解析股票名稱/代碼
  2. 透過 Bing 搜尋最近 4 季財報資料（SEC 10-Q/10-K、新聞稿）
  3. 將搜尋結果摘要寫入 docs/股票分析/<TICKER>_<DATE>/research.md
  4. 輸出引導提示，引導 AI Agent 完成完整分析報告

實際分析（閱讀財報、給出投資觀點）由 AI Agent 根據 research.md 內容完成。
"""

import os
import sys
import re
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────
# 1. 股票代碼對照表（常見）
# ─────────────────────────────────────────
KNOWN_TICKERS = {
    "輝達": "NVDA", "英偉達": "NVDA", "nvidia": "NVDA",
    "帕蘭泰爾": "PLTR", "palantir": "PLTR",
    "甲骨文": "ORCL", "oracle": "ORCL",
    "美滿電子": "MRVL", "marvell": "MRVL",
    "超微半導體": "AMD", "amd": "AMD",
    "英特爾": "INTC", "intel": "INTC",
    "特斯拉": "TSLA", "tesla": "TSLA",
    "蘋果": "AAPL", "apple": "AAPL",
    "谷歌": "GOOGL", "google": "GOOGL", "alphabet": "GOOGL",
    "微軟": "MSFT", "microsoft": "MSFT",
    "亞馬遜": "AMZN", "amazon": "AMZN",
    "meta": "META",
    "台積電": "TSM", "tsmc": "TSM",
    "博通": "AVGO", "broadcom": "AVGO",
    "康寧": "GLW", "corning": "GLW",
    "美光": "MU", "micron": "MU",
    "rocket lab": "RKLB", "小火箭": "RKLB",
    "優步": "UBER", "uber": "UBER",
    "crowdstrike": "CRWD",
    "cloudflare": "NET",
    "帕蘭泰爾": "PLTR",
    "snowflake": "SNOW",
    "servicenow": "NOW",
    "salesforce": "CRM",
}

QUARTER_MONTHS = {
    "Q1": "02", "Q2": "05", "Q3": "08", "Q4": "11"
}

# ─────────────────────────────────────────
# 2. 解析輸入 → ticker
# ─────────────────────────────────────────
def resolve_ticker(raw: str) -> str:
    raw = raw.strip()
    # 已經是代碼（全是字母）
    if re.fullmatch(r"[A-Za-z]{2,5}", raw):
        return raw.upper()
    # 嘗試對照表
    lower = raw.lower()
    if lower in KNOWN_TICKERS:
        return KNOWN_TICKERS[lower]
    # 去除常見前綴
    for prefix in ["股票", "分析", "輝", "nvidia"]:
        raw = raw.replace(prefix, "")
    raw = raw.strip()
    if raw.upper() in KNOWN_TICKERS.values():
        return raw.upper()
    if raw.lower() in KNOWN_TICKERS:
        return KNOWN_TICKERS[raw.lower()]
    # 未知 → 視為公司名，直接用原字
    return raw.upper()


# ─────────────────────────────────────────
# 3. 搜尋函式（使用 Bing 頁面讀取）
# ─────────────────────────────────────────
def bing_search(query: str, num_results: int = 8) -> list[dict]:
    """使用 Bing 搜尋引擎找資料"""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        params = {"q": query, "count": num_results}
        resp = requests.get(
            "https://bing.search.vi.aitoliaog.com/search",
            params=params,
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("webPages", {}).get("value", [])
            return [
                {"title": r.get("name", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")}
                for r in results
            ]
    except Exception:
        pass
    # fallback: 使用 subprocess curl
    try:
        cmd = [
            "curl", "-s", "--max-time", "10",
            "-H", "User-Agent: Mozilla/5.0",
            f'https://www.bing.com/search?q={query.replace(" ", "+")}&count={num_results}',
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return [{"title": "Bing result", "url": "", "snippet": result.stdout[:500]}]
    except Exception:
        return []


def search_earnings(ticker: str, company_name: str = "") -> dict:
    """搜尋最近 4 季財報相關資料"""
    queries = [
        # 季度財報
        (f'{ticker} Q3 2026 earnings report 10-Q OR 10-K', "Q3-2026"),
        (f'{ticker} Q2 2026 earnings report 10-Q', "Q2-2026"),
        (f'{ticker} Q1 2026 earnings report 10-Q', "Q1-2026"),
        (f'{ticker} fiscal year 2025 annual report 10-K', "FY2025"),
        # 財報電話會議
        (f'{ticker} Q3 2026 earnings call transcript', "Q3-2026-call"),
        (f'{ticker} Q2 2026 earnings call transcript', "Q2-2026-call"),
        # 新聞稿
        (f'{ticker} Q3 2026 revenue earnings press release', "Q3-2026-press"),
        # 前瞻指引
        (f'{ticker} Q4 2026 revenue guidance raised OR lowered', "Q4-guidance"),
        (f'{ticker} fiscal year 2026 2027 revenue forecast investor', "forecast"),
        # CEO/CFO 表述
        (f'{ticker} CEO OR CFO statement Q3 2026 outlook', "outlook"),
    ]

    results = {}
    for query, label in queries:
        hits = bing_search(query, num_results=5)
        results[label] = hits
        print(f"  [{label}] 找到 {len(hits)} 筆結果")

    return results


def search_sec_filing(ticker: str) -> list[dict]:
    """直接搜尋 SEC EDGAR 上的最新文件"""
    return bing_search(
        f'site:sec.gov "{ticker}" (10-Q OR 10-K) 2026',
        num_results=5
    )


# ─────────────────────────────────────────
# 4. 寫出 research.md
# ─────────────────────────────────────────
def write_research(ticker: str, company_name: str, search_results: dict) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    out_dir = Path("docs") / "股票分析" / f"{ticker}_{date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "research.md"

    now = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# {company_name}（{ticker}）財報資料彙整",
        f"> 自動蒐集日期：{now}｜使用工具：stocks_analysis.py｜請 AI Agent 閱讀後完成分析報告",
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
            lines.append(f"- URL：{url}" if url else "- URL：（無）")
            lines.append(f"- 摘要：{snippet}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines += [
        "## 備註",
        "",
        "以上為自動搜尋結果，請 AI Agent：",
        "1. 點擊相關連結，讀取完整財報內容（優先讀取 SEC 10-Q / 10-K 原文）",
        "2. 提取關鍵財務數據（營收、EPS、毛利率、指引等）",
        "3. 依據 `skills/prompts/stock_analysis_workflow.md` 中的框架完成分析報告",
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
    parser = argparse.ArgumentParser(description="股票財報分析 Workflow 入口")
    parser.add_argument("stock", nargs="+", help="股票名稱或代碼（可多個）")
    parser.add_argument("--ticker", help="手動指定股票代碼（如已知）")
    parser.add_argument("--name", help="公司名稱（可選）")
    args = parser.parse_args()

    raw_input = " ".join(args.stock)
    ticker = args.ticker or resolve_ticker(raw_input)
    company_name = args.name or raw_input

    print(f"\n{'='*50}")
    print(f"股票財報分析 Workflow")
    print(f"{'='*50}")
    print(f"輸入：{raw_input}")
    print(f"識別代碼：{ticker}")
    print(f"公司名稱：{company_name}")
    print()

    # Step 1: 搜尋 SEC 文件
    print("🔍 Step 1：搜尋 SEC 公告...")
    sec_results = search_sec_filing(ticker)
    for r in sec_results:
        print(f"  - {r['title']}")
        print(f"    {r['snippet'][:120]}")

    # Step 2: 搜尋財報資料
    print("\n🔍 Step 2：搜尋季度財報與電話會議...")
    earnings_results = search_earnings(ticker, company_name)

    # Step 3: 寫出 research.md
    print("\n📝 Step 3：寫出 research.md...")
    all_results = {"SEC_Filing": sec_results, **earnings_results}
    research_path = write_research(ticker, company_name, all_results)

    # Step 4: 提示
    print()
    print("=" * 50)
    print("✅ 資料蒐集完成！")
    print()
    print("請 AI Agent 依據以下步驟完成分析：")
    print(f"  1. 閱讀 {research_path}")
    print("  2. 點擊相關連結，讀取完整 10-Q / 10-K / 財報電話會議記錄")
    print("  3. 依據 `skills/prompts/stock_analysis_workflow.md` 框架完成分析")
    print(f"  4. 將報告儲存為 `docs/股票分析/{ticker}_*/analysis.md`")
    print()
    print("或直接執行 `/analyze_stock {ticker}` 交由 AI Agent 完成完整分析。")
    print("=" * 50)


if __name__ == "__main__":
    main()
