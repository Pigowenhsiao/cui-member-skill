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
    
    for filepath in summary_files:
        path_parts = filepath.split(os.sep)
        # 例如: ["docs", "會員直播", "20260717", "summary.md"]
        if len(path_parts) >= 4:
            video_type = path_parts[-3]
            date_dir = path_parts[-2]
            filename = path_parts[-1]
            
            # Gist 上的檔名：YYYYMMDD_VideoType.md
            gist_filename = f"{date_dir}_{video_type}.md"
            
            # 避免同資料夾內有多個 md 時互相覆蓋
            if gist_filename in files_payload:
                name, _ = os.path.splitext(filename)
                gist_filename = f"{date_dir}_{video_type}_{name}.md"
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    content = "\n" 
                files_payload[gist_filename] = {"content": content}
            print(f"已載入 {filepath} -> {gist_filename}")
            
    if not files_payload:
        print("沒有任何檔案需要同步，程式結束。")
        sys.exit(0)
        
    # 3. 呼叫 GitHub API 更新 Gist
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
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
