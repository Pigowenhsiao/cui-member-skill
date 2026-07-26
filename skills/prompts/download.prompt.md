---
mode: 'agent'
description: 'Step 1: 下載 YouTube 影片音訊與中繼資料'
---

## 任務：下載音訊 (Download Audio)

請根據使用者的作業系統（OS）使用對應的指令下載 YouTube 影片音訊：

### 🍎 Mac 版 (Apple Silicon / Intel)
```bash
uv run skills/download_audio.py "${input:url}"
```

### 🪟 Windows 版 (完全容器化)
Windows 採用全容器化運行，需先確保 `cui-tools` 容器已啟動 (`docker compose up -d` 或 `podman compose up -d`)。
請透過 `docker exec` (或 `podman exec`) 執行指令：
```bash
docker exec cui-tools uv run skills/download_audio.py "${input:url}"
```

### 執行後確認事項與自動化流程
1. 確認工作目錄下已生成 `.mp3` 音訊檔案與 `.info.json` 中繼資料檔案。
2. **自動進入後續處理流程**：在成功下載後，請你**自動並依序**執行接下來的處理步驟，直到完成摘要為止：
   - 執行 `/organize` 將音訊與中繼資料歸檔到對應的分類與日期資料夾。
   - 執行 `/transcribe` 對剛整理好的 `.mp3` 檔案進行語音轉文字。
   - 執行 `/summarize` 針對轉換出的文字稿 (`.txt`) 進行分析與摘要。
3. 全部完成後，向使用者回報流程執行完畢與各檔案產生的結果。

### 注意
- 預設會讀取 `.env` 中的 `COOKIES_PATH`（通常為 `./cookies.txt`）以下載會員限定影片。
- 如果下載失敗，請檢查 cookies 檔案是否存在且有效，並提醒使用者更新。
- 所有回覆請使用**繁體中文**。
