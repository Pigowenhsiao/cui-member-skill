---
mode: 'agent'
description: 'Step 3: 使用 Whisper 將音訊轉為文字稿'
---

## 任務：語音轉文字 (Transcription)

請根據使用者的作業系統（OS）使用對應的指令，將指定的音訊檔案轉為文字稿：

### 🍎 Mac 版 (Apple Silicon / Intel)
```bash
uv run skills/transcribe.py "${input:audioFilePath}"
```

### 🪟 Windows 版 (完全容器化)
Windows 採用全容器化運行，請透過 `docker exec` (或 `podman exec`) 執行指令（請注意路徑需為相對於工作目錄的路徑，如 `docs/會員直播/20260717/xxx.mp3`）：
```bash
docker exec cui-tools uv run skills/transcribe.py "${input:audioFilePath}"
```

### 執行後確認事項
1. 確認在音訊檔案的同一目錄下已生成同名的 `.txt` 文字稿檔案。
2. 向使用者回報轉譯結果，包含輸出檔案路徑與文字量概況。
3. 提示使用者可以接著執行 `/summarize` 來進行摘要分析。

### 🌐 字幕優先 (Subtitle-first) — 建議先嘗試

若該影片在 YouTube 上有**自動生成字幕**，應優先改用字幕作為文字稿來源：速度快（秒級 vs 分鐘級），且專有名詞、公司名、人名的正確率顯著優於 Whisper 離線轉譯。

```bash
# 由 YouTube URL 直接下載自動字幕（zh-Hant）並轉為純文字稿
uv run skills/subtitle_to_text.py "https://youtu.be/VIDEO_ID"

# 由本地已下載的 .vtt 轉換
uv run skills/subtitle_to_text.py path/to/VIDEO_ID.zh-Hant.vtt
```

**檢查影片是否有字幕**：
```bash
yt-dlp --list-subs --write-auto-subs "URL"
```

若字幕存在，`skills/subtitle_to_text.py` 會自動下載、剝除 VTT 行內標記、還原滾動式字幕的重複內容，並輸出與音訊同名的 `.txt`。輸出後即可直接進入 Step 4 摘要流程。

### 注意
- 該腳本會根據 `.env` 中的 `WHISPER_MODE` 自動選擇轉譯引擎：
  - `local`：使用本地 mlx-whisper（Apple Silicon Mac 專用）
  - `openai`：使用 OpenAI Whisper API
  - `azure`：使用 Azure OpenAI Whisper API
- 語言固定為中文 (`zh`)。
- 如果遇到 API 認證錯誤，請提醒使用者檢查 `.env` 中的 API Key 設定。
- 所有回覆請使用**繁體中文**。
