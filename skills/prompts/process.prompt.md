---
mode: 'agent'
description: '一鍵完成全頻道掃描與任務排程：掃描、下載、分類、轉文字、摘要、對比與同步 (全自動 orchestrator)'
---

## 任務：全自動頻道掃描與處理流水線 (Orchestrator)

這是一鍵執行命令，不需要任何參數。請你作為 Orchestrator，自動依序完成以下任務：

### 執行步驟

#### Step 1: 掃描小翠時政財經 (`/scan_cui`)
1. 執行 `/scan_cui` 任務 (參考 `skills/prompts/scan_cui.prompt.md`)。
2. 該任務會去檢查是否有最新影片，若有，會一路執行到摘要產生 (`/download` -> `/organize` -> `/transcribe` -> `/summarize`)。若沒有新影片，則會略過處理。
3. **請記錄**在 Step 1 中是否有真正下載並產生新的摘要 (`summary.md`)。

#### Step 2: 掃描美投侃新闻 (`/scan_meitou`)
1. 執行 `/scan_meitou` 任務 (參考 `skills/prompts/scan_meitou.prompt.md`)。
2. 該任務會去檢查是否有最新影片，若有，會一路執行到摘要產生 (`/download` -> `/organize` -> `/transcribe` -> `/summarize`)。若沒有新影片，則會略過處理。
3. **請記錄**在 Step 2 中是否有真正下載並產生新的摘要 (`summary.md`)。

#### Step 3: 條件判斷與後續處理
1. 如果在 **Step 1** 或 **Step 2** 中，**有任何一部新影片**被下載並產生了新摘要：
   - 執行 `/compare` (參考 `skills/prompts/compare.prompt.md`)，產生最新觀點對比的「每日新聞綜述」。
   - 執行 `/sync`，將結果同步至 Gist。
   - 執行 `/archive`，將結果同步至本地歸檔。
2. 如果 Step 1 與 Step 2 **都沒有**下載新影片，請向使用者回報「兩頻道皆無新影片，略過後續的對比與同步操作」，並結束此任務。

### 注意
- 所有回報與執行結果請使用**繁體中文**。
