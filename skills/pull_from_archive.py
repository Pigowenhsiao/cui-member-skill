# /// script
# dependencies = []
# ///

"""
將 archive 目錄下的 Git 存檔專案中的指定資料提取回本地端，
此為 /archive 流程的反向操作，且僅供手動執行。

使用方法:
  uv run skills/pull_from_archive.py
  docker exec cui-tools uv run skills/pull_from_archive.py
"""

import os
import sys
import shutil

ARCHIVE_DIR = "archive"
DOCS_DIR = "docs"
LOGS_FILE = os.path.join("logs", "download.log")
REQUIRED_DIRS = ["logs", "小翠時政財經", "美投君", "每日新聞綜述"]

def find_single_archive_project():
    """搜尋 archive 目錄下包含 .git 資料夾的 Git 存檔專案"""
    if not os.path.isdir(ARCHIVE_DIR):
        print(f"❌ 找不到目錄: {ARCHIVE_DIR}")
        sys.exit(1)

    projects = []
    for entry in os.listdir(ARCHIVE_DIR):
        project_path = os.path.join(ARCHIVE_DIR, entry)
        git_path = os.path.join(project_path, ".git")
        if os.path.isdir(project_path) and os.path.isdir(git_path):
            projects.append(project_path)
            
    if len(projects) == 0:
        print("❌ archive 目錄下未找到任何 Git 存檔專案。")
        sys.exit(1)
    elif len(projects) > 1:
        print(f"❌ 找到多個存檔專案 ({len(projects)} 個)。")
        for p in projects:
            print(f"   - {p}")
        print("請將 archive 目錄整理為僅剩下一個存檔專案後再重試。")
        sys.exit(1)
        
    return projects[0]

def validate_project_structure(project_path):
    """確保存檔專案包含必要的目錄"""
    missing = []
    for d in REQUIRED_DIRS:
        path = os.path.join(project_path, d)
        if not (os.path.isdir(path) or (d == "logs" and os.path.exists(path))):
            # 特別通融 logs 可能是只包含 download.log 的結構
            # 依需求 `logs`, `小翠時政財經`, `美投君`, `每日新聞綜述` 必須存在
            missing.append(d)
            
    # 檢查 logs/download.log
    archive_log = os.path.join(project_path, "logs", "download.log")
    if not os.path.exists(archive_log) and "logs" not in missing:
        print(f"⚠️ 警告: 專案中沒有 {archive_log}")
        
    if missing:
        print("❌ 存檔專案缺少以下必要目錄或檔案:")
        for m in missing:
            print(f"   - {m}")
        print("後續處理停止。")
        sys.exit(1)

def pull_logs(project_path):
    """讀取 archive 的 log 並追記至本地 log (簡易防重複)"""
    archive_log = os.path.join(project_path, "logs", "download.log")
    if not os.path.exists(archive_log):
        return

    # 讀取 Archive 最新 5 行
    with open(archive_log, "r", encoding="utf-8") as f:
        archive_lines = [line.strip() for line in f if line.strip()]
        
    latest_5 = archive_lines[-5:] if len(archive_lines) >= 5 else archive_lines
    if not latest_5:
        return

    # 讀取本地已存在的行 (用以防重複)
    existing_lines = set()
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    existing_lines.add(line.strip())
    else:
        os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
        
    # 追記
    appended_count = 0
    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        for line in latest_5:
            if line not in existing_lines:
                f.write(line + "\n")
                existing_lines.add(line)
                appended_count += 1
                
    if appended_count > 0:
        print(f"📄 成功追記 {appended_count} 筆紀錄至 {LOGS_FILE}")
    else:
        print(f"📄 最新 5 筆紀錄已存在，無新增紀錄 ({LOGS_FILE})")

def copy_directory_without_overwrite(src_dir, dest_dir):
    """遞迴複製目錄，若檔案已存在則跳過不覆蓋"""
    if not os.path.exists(src_dir):
        return 0
        
    copied_count = 0
    for root, dirs, files in os.walk(src_dir):
        # 計算相對路徑
        rel_path = os.path.relpath(root, src_dir)
        dest_root = os.path.join(dest_dir, rel_path) if rel_path != "." else dest_dir
        
        os.makedirs(dest_root, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)
                copied_count += 1
                print(f"  複製: {src_file} -> {dest_file}")
            else:
                pass # 檔案已存在，跳過
                
    return copied_count

def pull_docs(project_path):
    """將存檔中的頻道與綜述目錄複製到本地 docs/"""
    dirs_to_pull = ["小翠時政財經", "美投君", "每日新聞綜述", "預言命中率分析"]
    total_copied = 0
    
    for d in dirs_to_pull:
        src = os.path.join(project_path, d)
        dest = os.path.join(DOCS_DIR, d)
        
        if os.path.exists(src):
            print(f"📁 正在提取目錄: {d} ...")
            count = copy_directory_without_overwrite(src, dest)
            total_copied += count
            if count == 0:
                print(f"  (目錄內的所有檔案已存在，全部跳過)")
                
    print(f"📄 共複製了 {total_copied} 個檔案至 {DOCS_DIR}/。")

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("🔍 正在檢查 archive 目錄下的存檔專案...")
    project_path = find_single_archive_project()
    print(f"✅ 找到存檔專案: {project_path}")
    
    print("\n🔍 正在驗證專案目錄結構...")
    validate_project_structure(project_path)
    print("✅ 目錄結構驗證通過。")
    
    print("\n📦 開始提取資料...")
    pull_logs(project_path)
    pull_docs(project_path)
    
    print("\n🎉 提取完成！")

if __name__ == "__main__":
    main()
