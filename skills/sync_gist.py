# /// script
# dependencies = [
#   "requests",
#   "python-dotenv",
# ]
# ///

import os
import glob
import sys
import requests
from dotenv import load_dotenv

def main():
    # 載入 .env 變數
    load_dotenv()
    
    github_token = os.environ.get("GITHUB_TOKEN")
    gist_id = os.environ.get("GIST_ID")
    
    # 若為預設值或未設定，直接退出不報錯
    if not github_token or github_token == "your_github_token_here" or not gist_id or gist_id == "your_gist_id_here":
        print("提示：未同時設定 GITHUB_TOKEN 與 GIST_ID，跳過 Gist 同步。")
        sys.exit(0)
        
    print(f"準備同步至 Gist: {gist_id}...")
    
    files_payload = {}
    
    # 1. 讀取 GIST_README.md 作為 README.md
    readme_path = os.path.join("docs", "GIST_README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                content = "Empty README"
            files_payload["README.md"] = {"content": content}
        print("已載入 docs/GIST_README.md -> README.md")
    else:
        print("提示：未找到 docs/GIST_README.md，跳過 README 同步。")
        
    # 2. 讀取 keywords.md
    keywords_path = os.path.join("docs", "keywords.md")
    if os.path.exists(keywords_path):
        with open(keywords_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                content = "\n"
            files_payload["keywords.md"] = {"content": content}
        print("已載入 docs/keywords.md -> keywords.md")

    # 3. 讀取摘要筆記 (docs/*/*/*.md)
    # 預期結構: docs/<VideoType>/YYYYMMDD/*.md
    search_pattern = os.path.join("docs", "*", "*", "*.md")
    summary_files = glob.glob(search_pattern)
    
    if not summary_files:
        print("未找到任何摘要筆記 (*.md) 可供同步。")
    
    # 按照 video_type 進行分組，並找出最新的日期
    latest_files = {} # video_type -> (date_dir, [filepaths])
    for filepath in summary_files:
        path_parts = filepath.split(os.sep)
        # 例如: ["docs", "會員直播", "20260717", "summary.md"]
        if len(path_parts) >= 4:
            video_type = path_parts[-3]
            date_dir = path_parts[-2]
            
            if video_type not in latest_files:
                latest_files[video_type] = (date_dir, [filepath])
            else:
                current_latest_date = latest_files[video_type][0]
                if date_dir > current_latest_date:
                    latest_files[video_type] = (date_dir, [filepath])
                elif date_dir == current_latest_date:
                    latest_files[video_type][1].append(filepath)
            
    for video_type, (date_dir, filepaths) in latest_files.items():
        # Gist 上的檔名改為 VideoType.md，只保留最新的
        gist_filename = f"{video_type}.md"
        combined_content = f"> **最後更新**: {date_dir}\n\n"
        
        for filepath in sorted(filepaths):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    content = "\n" 
                
                # 若同日有多個檔案，加上檔案名稱作為子標題
                if len(filepaths) > 1:
                    filename = os.path.basename(filepath)
                    combined_content += f"## {filename}\n\n"
                
                combined_content += content + "\n\n"
                
        files_payload[gist_filename] = {"content": combined_content}
        print(f"已載入 {len(filepaths)} 個檔案 -> {gist_filename} (最新版本: {date_dir})")
            
    if not files_payload:
        print("沒有任何檔案需要同步，程式結束。")
        sys.exit(0)
        
    # 4. 呼叫 GitHub API 更新 Gist
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # 取得目前的 Gist 狀態，清理舊的冗餘檔案 (例如 YYYYMMDD_*.md)
    print("\n正在取得目前的 Gist 狀態以清理舊檔案...")
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        existing_files = get_response.json().get("files", {})
        for ext_filename in existing_files:
            # 如果是 .md 且不在本次更新清單內，且不是 README.md 或 keywords.md，就標記刪除
            if ext_filename.endswith(".md") and ext_filename not in files_payload:
                if ext_filename not in ["README.md", "keywords.md", "GIST_README.md"]:
                    print(f"標記刪除舊檔案: {ext_filename}")
                    files_payload[ext_filename] = None

    print("\n🚀 正在上傳至 GitHub Gist...")
    response = requests.patch(url, headers=headers, json={"files": files_payload})
    
    if response.status_code == 200:
        html_url = response.json().get("html_url", "")
        print(f"✅ 同步成功！\n檢視連結: {html_url}")
    else:
        print(f"❌ 同步失敗。HTTP 狀態碼: {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
