# AI Agent 專案操作指南 (AGENTS.md)

歡迎！身為一個 AI Agent（如 Claude、GitHub Copilot、Codex 或 Antigravity），當使用者要求你處理 YouTube 影片分析任務時，請遵循本指南中的工作流（Workflow）與工具（Skills）來完成任務。

## 專案概述
本專案提供了一套自動化腳本，用於將 YouTube 影片的音訊下載下來、轉譯為文字稿，並最終交由 AI Agent（也就是你）進行總結與投資分析。
所有操作應避免污染系統環境，並依賴 `uv run` 來隔離執行 Python 腳本。

## 你的核心任務與工作流程 (Workflow)

當使用者提供一個 YouTube URL，要求你進行下載、文字轉譯與總結時，請依序執行以下 4 個步驟：

### Step 1: 下載音訊 (Download Audio)
利用 `skills/download_audio.py` 下載影片音訊。
- **執行指令**：`uv run skills/download_audio.py "<YouTube_URL>"`
- 預設會讀取 `.env` 中的 `COOKIES_PATH`（通常為 `tmp/cookies.firefox-private.txt`）以下載會員限定影片。
- 執行後，工作目錄下將會生成 `.mp3` 檔案以及包含標題中繼資料的 `.info.json`。

### Step 2: 判斷與分類整理 (Categorization & Organizing)
**請發揮你的 AI 判斷能力！**
- 請讀取下載下來的 `.mp3` 檔名或 `.info.json` 內容。
- 根據影片「標題」與「頻道資訊」，推斷該影片的 **影片類型 (Video Type)**（例如：`會員直播`、`大盤分析`、`個股研究` 等，不要僅僅使用頻道名稱，請依據影片內容類型判斷）以及 **日期 (Date)**（例如：`20260717`）。
- **建立目錄**：根據你的判斷，建立對應的存放目錄，結構為 `./docs/<VideoType>/<Date>/`。
- **移動檔案**：將剛才下載的 `.mp3` 與 `.info.json` 移動到你建立的目錄下。

### Step 3: 語音轉文字 (Transcription)
利用 `skills/transcribe.py` 將整理好的音訊轉為文字。
- **執行指令**：`uv run skills/transcribe.py "./docs/<VideoType>/<Date>/<audio_filename>.mp3"`
- 該腳本會根據 `.env` 中的 `WHISPER_MODE`（`local`、`openai` 或 `azure`）進行文字轉譯，並在同一個目錄下生成同名的 `.txt` 文字稿檔案。
- **請確保文字稿與音訊檔存放在同一個分類資料夾中。**

### Step 4: 摘要與分析 (Summarization & Analysis)
這一步是你展現分析能力的時候。
- 閱讀剛才生成的文字稿（`.txt`）。
- 嚴格遵守 `skills/prompts/summarize.md` 中的指令。特別注意：**語音轉文字可能包含錯別字或同音異義詞，請根據上下文邏輯自行糾錯**。
- 將分析與摘要的結果，保存為 `./docs/<VideoType>/<Date>/summary.md`。

---

## 注意事項與規範
1. **無須依賴 Ollama**：摘要生成不再依賴本地 Ollama 腳本，而是直接由作為 AI Agent 的「你」來閱讀文本並產生 Markdown 報告。
2. **環境變數**：如果遇到認證或 API 錯誤，請檢查或提醒使用者 `.env` 的設定檔是否齊全。
3. **繁體中文輸出**：所有產生的資料夾名稱、分析報告以及與使用者的對話，請預設使用**繁體中文 (Traditional Chinese)**。
