---
mode: 'agent'
description: '自動掃描美投侃新闻最新影片，判斷是否已下載，若無則自動執行處理流程'
---

## 任務：自動掃描最新影片 (Auto-Scan)

請你執行 `/scan_meitou` 的自動化掃描任務。

### 執行步驟

#### Step 1: 取得最新影片資訊
1. 根據作業系統執行對應指令，取得「美投侃新闻」最新影片的標題與 URL：
   - **Mac**: `uv run skills/get_latest_video.py "https://www.youtube.com/@MeiTouNews/videos"`
   - **Windows**: `docker exec cui-tools uv run skills/get_latest_video.py "https://www.youtube.com/@MeiTouNews/videos"`
2. 腳本會返回 `<標題>|<URL>` 的格式。請解析出該影片的 **標題** 與 **URL**。

#### Step 2: 檢查是否已下載與處理
1. 從剛才取得的 **URL** 中提取出 YouTube 影片 ID（例如 `https://www.youtube.com/live/G0bWOrRYyDA` 與 `https://www.youtube.com/watch?v=G0bWOrRYyDA` 的影片 ID 皆為 `G0bWOrRYyDA`）。
2. 使用命令 `tail -n 20 logs/download.log` 讀取最近的下載紀錄，檢查該 **影片 ID** 是否已存在於紀錄中。
3. 判斷邏輯：
   - 若該影片 ID 已存在於 `logs/download.log` 之中，代表已經處理過。請向使用者回報「美投侃新闻：最新影片已處理過，無須重新下載」，並 **結束此任務**。
   - 若不存在，代表這是新的未處理影片，請進入 Step 3。

#### Step 3: 執行處理流程 (處理新影片)
既然這是一部新影片，請你自動針對剛取得的 **URL** 依序執行以下操作：
1. **下載**: 執行 `/download` (或使用 `skills/download_audio.py`) 下載音訊。
2. **分類**: 執行 `/organize` 將檔案移至 `docs/美投君/...`。
3. **轉譯**: 執行 `/transcribe` 產生文字稿。
4. **摘要**: 執行 `/summarize` 產生投資分析報告 (`summary.md`)。
5. **結束任務**: 若你是單獨執行 `/scan_meitou`，請到此（完成 `/summarize`）為止，向使用者回報「美投侃新闻：新影片已下載並完成摘要」，**不要**接著執行 `/scan_cui`、`/compare`、`/sync` 或 `/archive`。

### 注意
- 回報與執行結果請使用**繁體中文**。
