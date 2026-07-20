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

### 執行後確認事項
1. 確認工作目錄下已生成 `.mp3` 音訊檔案與 `.info.json` 中繼資料檔案。
2. 向使用者回報下載結果，包含檔案名稱與大小。
3. 提示使用者可以接著執行 `/organize` 來進行分類整理。

### 注意
- 預設會讀取 `.env` 中的 `COOKIES_PATH`（通常為 `./cookies.txt`）以下載會員限定影片。
- 如果下載失敗，請檢查 cookies 檔案是否存在且有效，並提醒使用者更新。
- 所有回覆請使用**繁體中文**。
