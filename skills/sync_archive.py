# /// script
# dependencies = [
#   "python-dotenv",
# ]
# ///

"""
archive 配下の Git プロジェクトに docs 内の .md ファイルをコピーし、
Git コミット＆プッシュを行うスクリプト。

使い方:
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
    """archive 配下の Git リポジトリ（.git ディレクトリを持つサブディレクトリ）を検索する"""
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
    """docs 配下の .md ファイルと keywords.md をアーカイブプロジェクトにコピーする"""
    copied_count = 0

    # 1. docs/**/*.md をコピー（ディレクトリ構造を維持）
    search_pattern = os.path.join(DOCS_DIR, "**", "*.md")
    md_files = glob.glob(search_pattern, recursive=True)

    for src_path in md_files:
        # docs/ からの相対パスを取得
        rel_path = os.path.relpath(src_path, DOCS_DIR)

        # GIST_README.md は後で README.md として別途処理するのでスキップ
        if os.path.basename(src_path) == "GIST_README.md":
            continue

        dest_path = os.path.join(project_path, rel_path)
        dest_dir = os.path.dirname(dest_path)

        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        copied_count += 1
        print(f"  コピー: {src_path} -> {dest_path}")

    # 2. GIST_README.md を README.md として上書きコピー
    gist_readme_path = os.path.join(DOCS_DIR, "GIST_README.md")
    if os.path.exists(gist_readme_path):
        readme_dest = os.path.join(project_path, "README.md")
        shutil.copy2(gist_readme_path, readme_dest)
        copied_count += 1
        print(f"  コピー: {gist_readme_path} -> {readme_dest} (README.md として上書き)")

    return copied_count


def git_commit_local(project_path):
    """Git add, commit を実行する（Push は手動で行うよう促す）"""
    try:
        # コンテナ環境では ownership の違いで git が拒否するため、safe.directory を設定
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

        # 変更があるかチェック
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print(f"  変更なし。コミットをスキップします。")
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
        print(f"  ✅ コミット完了: {commit_msg}")
        print(f"  ⚠️ セキュリティ保護のため、コンテナ内からの push は行いません。")
        print(f"  手動で `git push` を実行してください: {project_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git 操作エラー: {e}")
        if e.stderr:
            print(f"     {e.stderr.strip()}")
        return False


def main():
    print("🔍 archive 配下のアーカイブプロジェクトを検索中...")

    projects = find_archive_projects()

    if not projects:
        print("archive 配下にアーカイブ用プロジェクトが見つかりません。何もしません。")
        sys.exit(0)

    print(f"📦 {len(projects)} 個のアーカイブプロジェクトが見つかりました。\n")

    for project_path in projects:
        project_name = os.path.basename(project_path)
        print(f"--- [{project_name}] ---")

        # docs の .md ファイルをコピー
        copied = copy_docs_to_project(project_path)
        if copied == 0:
            print(f"  コピー対象のファイルがありません。スキップします。")
            continue

        print(f"  📄 {copied} 個のファイルをコピーしました。")

        # Git コミット
        git_commit_local(project_path)
        print()

    print("🎉 アーカイブ同期完了！")


if __name__ == "__main__":
    main()
