# AI Agent 專案操作指南 (AGENTS.md)

歡迎！身為一個 AI Agent（如 Claude、GitHub Copilot、Codex 或 Antigravity），當使用者要求你處理 YouTube 影片分析任務時，請遵循本指南中的工作流（Workflow）與工具（Skills）來完成任務。

## 專案概述
本專案提供 YouTube 影片掃描、字幕／音訊取得、文字稿與 AI 分析工具，預設涵蓋「小翠時政財經」、「美投侃新聞」與「美投講美股」三個頻道。
Python 腳本使用 `uv run` 執行；原生 Windows/Linux 的本地語音轉錄基線為 CPU faster-whisper。

## 你的核心任務與工作流程 (Workflow)

使用者執行 `/process` 時，依 `skills/prompts/process.prompt.md` 掃描三頻道並逐支處理。掃描錯誤不可解讀成沒有新影片。

> **快速指令參考 (Slash Commands)**
> 每個步驟均可透過 `/` 命令獨立執行：
> | 命令 | 步驟 | 必要輸入 |
> |------|------|----------|
> | `/process` | 掃描三個預設頻道，逐支字幕優先處理並產生分析；遵照 process 指引 | （無） |
> | `/scan_cui` | 獨立掃描「小翠時政財經」 | （無） |
> | `/scan_meitou` | 獨立掃描「美投侃新聞」與「美投講美股」 | （無） |
> | `/download` | 直接下載影片音訊 | YouTube URL |
> | `/organize` | 根據頻道／標題分類並安全命名 | 影片資訊 |
> | `/transcribe` | 對本地 MP3 產生文字稿（process 已自動字幕優先） | `.mp3` 路徑 |
> | `/summarize` | 依 `skills/templates/summarize_template.md` 分析文字稿 | `.txt` 路徑 |
> | `/compare` | 依 `skills/templates/compare_template.md` 比較可用摘要 | （無） |
> | `/sync` | 選擇性執行 `uv run skills/sync_gist.py` | （無） |
> | `/archive` | 選擇性執行 `uv run skills/sync_archive.py` | （無） |
> | `/analyze_stock` | 美股財報分析：輸入股票名稱/代碼，上網搜尋最近 4 季財報並完成價值投資框架分析 | 股票名稱或代碼 |
> | `/analyze_twstock` | 台股財報分析：輸入台股代碼（4位數）或名稱，上網搜尋財報、月營收、新聞，完成台股價值投資框架分析 | 台股代碼（如 2330）或名稱（如 台積電）|

### 自動掃描與 `/process`

`/process` 的可執行流程與錯誤處理詳見 `skills/prompts/process.prompt.md`。從專案根目錄執行掃描：

```bash
uv run skills/list_new_videos.py --format json
```

只把掃描成功且 JSON 解析成功視為有效結果；Cookie、網路或其他錯誤不是「沒有新影片」。掃描預設涵蓋上述三個頻道，只過濾 SQLite 已明確提交摘要的影片；`transcript_ready` 仍會出現在下次掃描，`logs/download.log` 不代表完整處理。

對每支待處理影片執行：

```bash
uv run skills/process_video.py "<url>" --video-id "<id>" --title "<title>" --channel-key "<channel_key>"
```

此處理器先嘗試人工字幕，再自動字幕；語言依繁體中文、其他中文、英文排序。把掃描 JSON 的 `channel_key` 原樣傳入，避免泛用頻道名稱造成錯誤分類。字幕可用時直接產生文字稿並跳過音訊與 Whisper；字幕不可用時才下載 MP3 並呼叫 `skills/transcribe.py`。成功只會標記 `transcript_ready`；摘要檔寫入後必須再執行 `uv run skills/process_video.py "<url>" --video-id "<id>" --title "<title>" --channel-key "<channel_key>" --mark-summarized`，確認 `.txt` 與同名 `.md` 存在才標記 `complete`。摘要中斷可重試而不必重做字幕、音訊或轉錄。
報告採用 `skills/templates/summarize_template.md`，檔名為安全化影片資料夾名稱加 `.md`；比較採用 `skills/templates/compare_template.md`，沒有足夠摘要時不得虛構內容。

Gist 與 archive 同步皆是選擇性操作，分別執行：

```bash
uv run skills/sync_gist.py
uv run skills/sync_archive.py
```

Gist 需要有效的 `GITHUB_TOKEN` 與 `GIST_ID`。僅使用 repository 中存在的同步工具；目前未配置 Vault 同步流程。

---

## 注意事項與規範
1. **無須依賴 Ollama**：摘要生成不再依賴本地 Ollama 腳本，而是直接由作為 AI Agent 的「你」來閱讀文本並產生 Markdown 報告。
2. **環境變數**：如果遇到認證或 API 錯誤，請檢查或提醒使用者 `.env` 的設定檔是否齊全。
3. **繁體中文輸出**：所有產生的資料夾名稱、分析報告以及與使用者的對話，請預設使用**繁體中文 (Traditional Chinese)**。
4. **絕對禁止污染系統環境**：身為 AI Agent，你在此專案中**發誓**執行任何 Python 腳本或安裝套件時，**絕對只使用 `uv`**（例如 `uv run`、`uv pip install` 等），**絕不使用系統全局的 `python` 或 `pip` 指令**，以確保系統環境不被污染。
