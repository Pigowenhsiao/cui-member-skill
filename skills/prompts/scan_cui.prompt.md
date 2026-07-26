---
mode: 'agent'
description: '自動掃描小翠時政財經最新影片，判斷是否已下載，若無則自動執行處理流程'
---

## 任務：自動掃描最新影片 (Auto-Scan)

請你執行 `/scan_cui` 的自動化掃描任務。

### 執行步驟

#### Step 1: 取得最新影片資訊
1. 根據作業系統執行對應指令，取得「小翠時政財經」最新直播影片的標題與 URL：
   - **Mac**: `uv run skills/get_latest_video.py "https://www.youtube.com/@cui_news/streams"`
   - **Windows**: `docker exec cui-tools uv run skills/get_latest_video.py "https://www.youtube.com/@cui_news/streams"`
2. 腳本會返回 `<標題>|<URL>` 的格式。請解析出該影片的 **標題** 與 **URL**。

#### Step 2: 檢查是否已下載與處理
1. 在專案中搜尋 `docs/小翠時政財經/` 及其子目錄（如 `會員直播`、`每日要聞`），找出最新的幾篇 `summary.md`。
2. 閱讀這些 `summary.md` 檔案，檢查其中是否已包含剛才取得的**標題**或 **URL**。
   - 若該影片已存在於最新的 `summary.md` 之中，代表已經處理過。請向使用者回報「小翠時政財經：最新影片已處理過，無須重新下載」，並 **結束此任務**。
   - 若不存在，代表這是新的未處理影片，請進入 Step 3。

#### Step 3: 執行處理流程 (處理新影片)
既然這是一部新影片，請你自動針對剛取得的 **URL** 依序執行以下操作：
1. **下載**: 執行 `/download` (或使用 `skills/download_audio.py`) 下載音訊。
2. **分類**: 執行 `/organize` 將檔案移至 `docs/小翠時政財經/...`。
3. **轉譯**: 執行 `/transcribe` 產生文字稿。
4. **摘要**: 執行 `/summarize` 產生投資分析報告 (`summary.md`)。
5. 完成後，向使用者回報「小翠時政財經：新影片已下載並完成摘要」。

### 注意
- 回報與執行結果請使用**繁體中文**。
