# `/process` 工作流程

`/process` 預設只掃描以下三個頻道，不能把它縮成雙頻道：

1. 小翠時政財經（包含直播與每日要聞）
2. 美投侃新聞
3. 美投講美股

## 逐支處理

1. 從專案根目錄執行 `uv run skills/list_new_videos.py --format json`。確認掃描成功並讀取所有 `groups[].videos[]`。非零結束、Cookie 錯誤或網路錯誤均是掃描失敗，不可當成「沒有新影片」；停止後回報錯誤。
2. 對每支影片呼叫：

   ```text
   uv run skills/process_video.py "<url>" --video-id "<id>" --title "<title>" --channel-key "<channel_key>"
   ```

   透過 argv/終端工具的參數陣列傳遞值，不要自行拼接未跳脫的 shell 命令。腳本安全化資料夾名稱，先下載可用字幕；只有無可用字幕或字幕下載失敗時才下載 MP3 並執行 Whisper。文字稿階段完成時狀態為 `transcript_ready`，尚未算完整處理；只有已存在同資料夾報告並提交完成狀態後，掃描器才會略過該影片。下載日誌不是處理完成的依據。
3. 若單支影片處理失敗，保留錯誤訊息與字幕失敗細節，繼續處理其他影片；下一次掃描會再次列出未完成影片，處理器會略過已完成階段。
4. 閱讀成功產生的 UTF-8 `.txt`。如果安全資料夾內尚無報告，依 `skills/templates/summarize_template.md` 產生同資料夾報告，檔名為完整安全資料夾名稱加 `.md`；不要覆寫已存在的報告或其他影片資料。報告存在後才執行完成提交：

   ```text
   uv run skills/process_video.py "<url>" --video-id "<id>" --title "<title>" --channel-key "<channel_key>" --mark-summarized
   ```

   此命令會確認 `.txt` 與同名 `.md` 都存在後才將狀態標記為 `complete`。若摘要中斷，下次 `/process` 會再次列出 `transcript_ready` 影片並從摘要檢查／重試開始，不會重抓字幕、重下載 MP3 或重做轉錄。
5. 完成所有可處理影片後，才使用 `skills/templates/compare_template.md` 產生適用的每日觀點比較。沒有足夠的兩方摘要時，不要虛構比較內容。
6. Gist 與 archive 同步是可選步驟，只能在使用者要求或專案工作指示要求時執行。現有指令為 `uv run skills/sync_gist.py` 與 `uv run skills/sync_archive.py`；Gist 需要 `.env` 中有效的 `GITHUB_TOKEN` 和 `GIST_ID`。不要呼叫 repository 中不存在的同步腳本。

## 輸出與回報

報告原文使用繁體中文。完成時列出掃描的三個頻道、已處理／失敗影片及輸出路徑；若掃描失敗，清楚回報錯誤且不要宣稱沒有新影片。Cookies、網路或轉錄失敗不得以空結果或虛構文字稿取代。
