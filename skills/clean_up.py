"""
清理 docs 目錄下所有非 .md 的檔案（例如 .mp3、.txt、.info.json 等），保留 .gitkeep 與 .keep。

預設僅列出對象檔案的數量與合計大小，不會刪除任何檔案；
必須明確加上 --delete、--force 或 --yes 參數才會執行刪除。

使用方法:
  uv run skills/clean_up.py            # 僅統計（預設，不刪除）
  uv run skills/clean_up.py --list     # 統計並列出所有對象檔案
  uv run skills/clean_up.py --delete   # 實際刪除對象檔案
    uv run skills/clean_up.py --force  # 強制刪除對象檔案
    uv run skills/clean_up.py --yes    # 確認刪除對象檔案
"""

import argparse
import os
import sys

DOCS_DIR = "docs"


def find_targets():
    """遞迴搜尋 docs 目錄下非 .md 檔案，並保留 .gitkeep 與 .keep"""
    targets = []
    for root, _dirs, files in os.walk(DOCS_DIR):
        for name in files:
            if name not in {".gitkeep", ".keep"} and not name.lower().endswith(".md"):
                targets.append(os.path.join(root, name))
    return sorted(targets)


def human_size(num_bytes):
    """將位元組數轉為易讀的單位字串"""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


def main():
    parser = argparse.ArgumentParser(description="清理 docs 目錄下的非 .md 檔案")
    parser.add_argument("--list", action="store_true", help="列出所有對象檔案")
    parser.add_argument(
        "--delete", "--force", "--yes", dest="delete", action="store_true",
        help="刪除對象檔案（預設不刪除）",
    )
    args = parser.parse_args()

    if not os.path.isdir(DOCS_DIR):
        print(f"❌ 找不到 {DOCS_DIR} 目錄，請於專案根目錄執行。")
        sys.exit(1)

    targets = find_targets()
    total_size = sum(os.path.getsize(p) for p in targets)

    print(f"📂 對象檔案數：{len(targets)}")
    print(f"📦 合計大小：{human_size(total_size)} ({total_size} bytes)")

    if args.list:
        for path in targets:
            print(f"  - {path} ({human_size(os.path.getsize(path))})")

    if not targets:
        print("✅ 沒有需要清理的檔案。")
        return

    if not args.delete:
        print("ℹ️ 未指定 --delete，未刪除任何檔案。")
        return

    deleted, failed = 0, 0
    for path in targets:
        try:
            os.remove(path)
            deleted += 1
        except OSError as e:
            failed += 1
            print(f"⚠️ 刪除失敗：{path}（{e}）")

    print(f"🗑️ 已刪除 {deleted} 個檔案，失敗 {failed} 個。")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
