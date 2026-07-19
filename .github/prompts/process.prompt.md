---
mode: 'agent'
description: '一鍵完成所有任務：下載、分類、轉文字與摘要分析 (全自動)'
---

## 任務：全自動影片處理流水線 (End-to-End Pipeline)

這是一鍵執行命令。請你自動依序完成 Step 1 到 Step 4，處理使用者指定的 YouTube 影片。

### 執行步驟

#### Step 1: 下載音訊
1. 執行指令：`uv run skills/download_audio.py "${input:url}"`
2. 等待下載完成，確保工作目錄生成了 `.mp3` 與 `.info.json` 檔案。

#### Step 2: 判斷與分類整理
1. 讀取剛才下載的 `.info.json` 內容或從 `.mp3` 檔名提取資訊。
2. 根據標題與頻道資訊推斷 **影片類型 (Video Type)** 與 **日期 (Date)**（格式：`YYYYMMDD`）。
3. 建立分類目錄：`./docs/<VideoType>/<Date>/`。
4. 將 `.mp3` 與 `.info.json` 移動到該分類目錄下。

#### Step 3: 語音轉文字
1. 針對剛移動好的檔案，執行指令：`uv run skills/transcribe.py "./docs/<VideoType>/<Date>/<目標音訊檔>.mp3"`
2. 等待轉譯完成，確認同目錄下已生成同名的 `.txt` 文字稿檔案。

#### Step 4: 摘要與分析
1. 閱讀剛才生成的文字稿（`.txt`）。
2. 嚴格遵守 `#file:skills/prompts/summarize.md` 中的所有指令。
3. ⚠️ **特別注意：語音轉文字的文本可能包含錯別字、漏字或同音異義詞**，請發揮 AI 判斷力進行合理推斷與糾錯，尤其是財經術語與數字。
4. 將生成的 Markdown 報告保存為 `./docs/<VideoType>/<Date>/summary.md`。

### 執行後確認事項
- 向使用者回報任務完成，並提供最終的分析重點與結論。
- 告知所有檔案（音訊、原稿、摘要報告）均已儲存至目標目錄中。
- 所有回覆請使用**繁體中文**。
