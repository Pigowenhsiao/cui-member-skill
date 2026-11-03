# STATUS_ALL

## 字幕優先與 Windows/Linux 相容修正
- **變更：** 新增字幕優先處理與 MP3/Whisper fallback；加入 UTF-8 VTT 轉換、Windows 安全檔名與 UTF-16 長度限制、SQLite 階段重試、穩定頻道鍵分類；更新流程提示、文件、CPU Compose 設定及迴歸測試。保留既有 `docs/` 報告與 Cookie 資料。
- **QA：** 第五輪獨立 QA 評分 97/100，通過（門檻 >95）。第三輪所提 `docs/` 報告差異經確認為工作開始前已存在的使用者變更，未回復或覆寫。
- **驗證：** `uv run --with python-dotenv --with yt-dlp -m unittest discover -s tests -p test_video_pipeline.py`：13 tests，OK。`uv run skills/subtitle_to_text.py /tmp/cui-member-skill-smoke.vtt`：成功產生 UTF-8 文字稿並確認內容。`uv run skills/process_video.py --help`：成功。
- **驗證修正：** 初次直接執行測試檔未能匯入 `skills`；改用 unittest discovery 執行後，修正測試中的缺少匯入與 patch 範圍問題。另修正 SQLite 連線未關閉及其匯入，最後測試通過且未再出現 ResourceWarning。
- **限制：** 本次執行環境為 Linux；未在原生 Windows 主機實際執行。未執行需 YouTube 網路／Cookie 的線上整合下載。
- **下一步：** 在 Windows 原生環境執行同一套迴歸測試與一支實際字幕下載流程；確認 Windows 的 `uv`、cookies 和 `yt-dlp` 外部依賴設定。
