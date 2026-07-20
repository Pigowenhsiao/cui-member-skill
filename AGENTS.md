# AI Agent 專案操作指南 (AGENTS.md)

歡迎！身為一個 AI Agent（如 Claude、GitHub Copilot、Codex 或 Antigravity），當使用者要求你處理 YouTube 影片分析任務時，請遵循本指南中的工作流（Workflow）與工具（Skills）來完成任務。

## 專案概述
本專案提供了一套自動化腳本，用於將 YouTube 影片的音訊下載下來、轉譯為文字稿，並最終交由 AI Agent（也就是你）進行總結與投資分析。
所有操作應避免污染系統環境，並依賴 `uv run` 來隔離執行 Python 腳本。

## 你的核心任務與工作流程 (Workflow)

當使用者提供一個 YouTube URL，要求你進行下載、文字轉譯與總結時，請依序執行以下 5 個步驟：

> **快速指令參考 (Slash Commands)**
> 每個步驟均可透過 `/` 命令獨立執行：
> | 命令 | 步驟 | 必要輸入 |
> |------|------|----------|
> | `/process` | 一鍵執行所有步驟 (Step 1~6) | YouTube URL |
> | `/download` | Step 1: 下載音訊 | YouTube URL |
> | `/organize` | Step 2: 分類整理 | `.mp3` 檔案路徑 |
> | `/transcribe` | Step 3: 語音轉文字 | `.mp3` 檔案路徑 |
> | `/summarize` | Step 4: 摘要分析 | `.txt` 檔案路徑 |
> | `/sync` | Step 5: 同步至 Gist | （無） |
> | `/archive` | Step 6: アーカイブ同期 | （無） |

### 一鍵完整處理 (End-to-End) — `/process`
如果你希望 AI Agent 自動幫你包辦所有事情，請使用 `/process` 指令並提供 YouTube URL。Agent 將會為你依序執行以下的 Step 1 到 Step 6。
> **參閱文件**：`skills/prompts/process.prompt.md`

### Step 1: 下載音訊 (Download Audio) — `/download`
利用 `yt-dlp` 下載影片音訊。
> **參閱文件**：`skills/prompts/download.prompt.md`

### Step 2: 判斷與分類整理 (Categorization & Organizing) — `/organize`
**請發揮你的 AI 判斷能力！**
根據影片「標題」與「頻道資訊」，推斷該影片的 **影片類型 (Video Type)** 與 **日期 (Date)**，建立目錄並移動檔案。
> **參閱文件**：`skills/prompts/organize.prompt.md`

### Step 3: 語音轉文字 (Transcription) — `/transcribe`
利用 `skills/transcribe.py` 將整理好的音訊轉為文字。
> **參閱文件**：`skills/prompts/transcribe.prompt.md`

### Step 4: 摘要與分析 (Summarization & Analysis) — `/summarize`
這一步是你展現分析能力的時候。
閱讀指定的文字稿（`.txt`），並根據提示詞生成分析報告。
> **參閱文件**：`skills/prompts/summarize.prompt.md` 以及 `skills/prompts/summarize.md`

### Step 5: 同步至 Gist (Sync to Gist) — `/sync`
將生成的重點筆記自動同步至 GitHub Gist。
根據作業系統執行對應指令：
- **Mac**: `uv run skills/sync_gist.py`
- **Windows**: `docker exec cui-tools uv run skills/sync_gist.py`
> 執行前請確保 `.env` 中已設定 `GITHUB_TOKEN` 與 `GIST_ID`。

### Step 6: アーカイブ同期 (Sync to Archive) — `/archive`
`./archive` 配下に Git プロジェクトが存在する場合、`docs` 内の `.md` ファイルをコピーし、Git コミット＆プッシュを行う。
根據作業系統執行對應指令：
- **Mac**: `uv run skills/sync_archive.py`
- **Windows**: `docker exec cui-tools uv run skills/sync_archive.py`
> `./archive` 配下にプロジェクトが存在しない場合は何もしない。

---

## 注意事項與規範
1. **無須依賴 Ollama**：摘要生成不再依賴本地 Ollama 腳本，而是直接由作為 AI Agent 的「你」來閱讀文本並產生 Markdown 報告。
2. **環境變數**：如果遇到認證或 API 錯誤，請檢查或提醒使用者 `.env` 的設定檔是否齊全。
3. **繁體中文輸出**：所有產生的資料夾名稱、分析報告以及與使用者的對話，請預設使用**繁體中文 (Traditional Chinese)**。
4. **絕對禁止污染系統環境**：身為 AI Agent，你在此專案中**發誓**執行任何 Python 腳本或安裝套件時，**絕對只使用 `uv`**（例如 `uv run`、`uv pip install` 等），**絕不使用系統全局的 `python` 或 `pip` 指令**，以確保系統環境不被污染。
