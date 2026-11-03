# /// script
# dependencies = [
#   "python-dotenv",
# ]
# ///

"""
將 archive 目錄下的 Git 專案與 docs 內的 .md 檔案同步，
並執行 Git 提交（不自動 Push，以確保安全性）。

使用方法:
  uv run skills/sync_archive.py
  docker exec cui-tools uv run skills/sync_archive.py
"""

import os
import sys
import glob
import shutil
import subprocess


ARCHIVE_DIR = "archive"
DOCS_DIR = "docs"


def find_archive_projects():
    """搜尋 archive 目錄下包含 .git 資料夾的 Git 存檔專案"""
    if not os.path.isdir(ARCHIVE_DIR):
        return []

    projects = []
    for entry in os.listdir(ARCHIVE_DIR):
        project_path = os.path.join(ARCHIVE_DIR, entry)
        git_path = os.path.join(project_path, ".git")
        if os.path.isdir(project_path) and os.path.isdir(git_path):
            projects.append(project_path)
    return projects


def copy_docs_to_project(project_path):
    """將 docs 目錄下的 .md 檔案複製至存檔專案（維持目錄結構）"""
    copied_count = 0

    # 1. 複製 docs/**/*.md（維持原始目錄結構）
    search_pattern = os.path.join(DOCS_DIR, "**", "*.md")
    md_files = glob.glob(search_pattern, recursive=True)

    for src_path in md_files:
        # 取得相對於 docs/ 的路徑
        rel_path = os.path.relpath(src_path, DOCS_DIR)

        # GIST_README.md 另行作為 README.md 處理，此處跳過
        if os.path.basename(src_path) == "GIST_README.md":
            continue

        dest_path = os.path.join(project_path, rel_path)
        dest_dir = os.path.dirname(dest_path)

        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        copied_count += 1
        print(f"  複製: {src_path} -> {dest_path}")

    # 2. 將 GIST_README.md 複製為 README.md（覆蓋寫入）
    gist_readme_path = os.path.join(DOCS_DIR, "GIST_README.md")
    if os.path.exists(gist_readme_path):
        readme_dest = os.path.join(project_path, "README.md")
        shutil.copy2(gist_readme_path, readme_dest)
        copied_count += 1
        print(f"  複製: {gist_readme_path} -> {readme_dest}（作為 README.md 覆蓋寫入）")

    return copied_count


def git_commit_local(project_path):
    """執行 Git add 與 commit（不執行 Push，請手動推送）"""
    try:
        # 容器環境中可能因目錄擁有者不同而被 git 拒絕，先設定 safe.directory
        abs_project_path = os.path.abspath(project_path)
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", abs_project_path],
            capture_output=True,
            text=True,
        )

        # git add .
        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            check=True,
            capture_output=True,
            text=True,
        )

        # 確認是否有變更
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print(f"  無任何變更，略過提交。")
            return False

        # git commit
        from datetime import datetime

        commit_msg = f"docs: 摘要同步更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=project_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"  ✅ 提交完成: {commit_msg}")
        print(f"  ⚠️  為確保安全性，不在容器內自動執行 Push。")
        print(f"  請手動執行 `git push`：{project_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git 操作錯誤: {e}")
        if e.stderr:
            print(f"     {e.stderr.strip()}")
        return False


def copy_logs_to_project(project_path):
    """將 logs/download.log 的最新 5 筆紀錄複製至存檔專案"""
    log_src = os.path.join("logs", "download.log")
    if not os.path.exists(log_src):
        return 0

    with open(log_src, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    latest_5 = lines[-5:] if len(lines) >= 5 else lines
    if not latest_5:
        return 0

    log_dest = os.path.join(project_path, "logs", "download.log")
    os.makedirs(os.path.dirname(log_dest), exist_ok=True)

    with open(log_dest, "w", encoding="utf-8") as f:
        f.writelines(latest_5)

    print(f"  複製: {log_src} (最新 5 筆) -> {log_dest}（覆蓋寫入）")
    return 1


def main():
    print("🔍 正在搜尋 archive 目錄下的存檔專案...")

    projects = find_archive_projects()

    if not projects:
        print("archive 目錄下未找到任何存檔專案，略過同步。")
        sys.exit(0)

    print(f"📦 找到 {len(projects)} 個存檔專案。\n")

    for project_path in projects:
        project_name = os.path.basename(project_path)
        print(f"--- [{project_name}] ---")

        # 複製 docs 內的 .md 檔案
        copied = copy_docs_to_project(project_path)
        
        # 複製 logs/download.log 最新 5 筆
        copied += copy_logs_to_project(project_path)

        if copied == 0:
            print(f"  沒有可複製的檔案，略過此專案。")
            continue

        print(f"  📄 已處理 {copied} 個檔案。")

        # 執行 Git 提交
        git_commit_local(project_path)
        print()

    print("🎉 存檔同步完成！")


if __name__ == "__main__":
    main()
