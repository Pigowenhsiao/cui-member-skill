# CUI Member Skill

本專案提供了一套自動化工具與工作流（Skills），旨在將特定 YouTube 頻道（包括會員限定影片）的音訊下載、轉譯為文字，並透過 AI Agent（如 Claude、GitHub Copilot、Codex 或 Antigravity）進行重點摘要與投資分析整理。

## 專案設計理念
- **AI Agent 優先 (Agent-centric)**：專案中的功能被封裝為一系列的 Scripts (Skills)，設計初衷是交由 AI Agent 閱讀 `AGENTS.md` 後自動呼叫與執行，而非完全依賴人類手動輸入指令。
- **環境隔離**：所有 Python 腳本皆使用 `uv` 管理內聯依賴（Inline dependencies），確保不污染系統全域環境。
- **靈活的模型切換**：文字轉譯功能（Whisper）支援本地端運算（Mac Apple Silicon 專用的 mlx-whisper，非 ARM Mac 環境則會自動降級為 CPU 版的 `faster-whisper` 搭配 `medium` 模型運作）以及雲端 API（OpenAI, Azure）。

---

## 前置需求與安裝

### 1. 安裝系統工具
本專案依賴 `yt-dlp` 下載音訊，以及 `uv` 執行隔離的 Python 腳本。
```bash
# macOS (使用 Homebrew)
brew install yt-dlp
brew install uv
```

### 2. 準備 Cookies 檔案 (抓取會員限定影片)
如需下載會員專屬內容，需要提供瀏覽器的 Cookies。
- **取得方式**：安裝 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 等擴充功能，將 YouTube 的 cookies 匯出為 `cookies.txt`。
- **放置位置**：將該檔案放置於專案的 `tmp/cookies.firefox-private.txt`。
- **注意**：該檔案包含敏感登入資訊，已被加入 `.gitignore` 中，**請勿將其提交至 Git**。

### 3. 環境變數設定
複製環境變數範本並根據需求進行修改：
```bash
cp .env.example .env
```
在 `.env` 中，您可以設定：
- `WHISPER_MODE`: 切換轉譯模式 (`local`, `openai`, `azure`)
- `OPENAI_API_KEY`: 若使用 API 模式則必填

---

## 使用方法 (Workflow)

要開始進行影片分析，**最推薦的方式是直接將 YouTube URL 貼給您的 AI Agent（如本聊天視窗中的 AI），並請它根據專案內的 `AGENTS.md` 執行任務。**

### 手動執行步驟（供參考）
若您希望自行手動執行，請依序呼叫以下腳本：

**1. 下載音訊與標題中繼資料**
```bash
uv run skills/download_audio.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

**2. 建立分類目錄並移動檔案**
依據下載下來的標題，手動建立分類目錄（例如：`./docs/會員直播/20260717/`），並將 `.mp3` 移入。

**3. 語音轉文字**
```bash
uv run skills/transcribe.py "./docs/會員直播/20260717/audio_file.mp3"
```

**4. 總結與分析**
參考 `skills/prompts/summarize.md` 的提示詞，將轉譯出的 `.txt` 文字稿交由 LLM 生成摘要報告。

---

## 專案結構

```
cui-member-skill/
├── AGENTS.md                  # 給 AI Agent 閱讀的自動化操作手冊
├── README.md                  # 本文件
├── .env.example               # 環境變數設定範本
├── .gitignore                 
├── docker-compose.yml         # Windows Nvidia GPU 專用的 Docker 配置 (Ollama & Whisper-gpu)
├── skills/                    # 自動化技能腳本區
│   ├── download_audio.py      # 音訊與元數據下載
│   ├── transcribe.py          # 語音轉文字 (支援 Local/OpenAI/Azure，並有 CPU/GPU 自動適應)
│   └── prompts/
│       └── summarize.md       # 給 LLM 的分析提示詞範本
├── docs/                      # 產出目錄（按 影片類型/日期 分類存放）
└── tmp/
    └── cookies.firefox-private.txt  # 存放使用者的 Cookies (Git 忽略)
```

---

## 附錄：Windows / NVIDIA GPU (CUDA) 容器執行指南

若您在 Windows 上擁有 NVIDIA 顯示卡，可以透過 Docker 完整使用 GPU 加速來進行本機端 Whisper 轉譯與 Ollama 推論。

### 1. 啟動 GPU 容器環境
確認已安裝 WSL2 與 Docker Desktop (含 NVIDIA Container Toolkit)。
於專案目錄執行：
```bash
docker-compose up -d
```
這會啟動內建 NVIDIA GPU 支援的 `ollama` 與 `whisper-gpu` 容器。

### 2. 下載本地 LLM 模型 (Ollama)
```bash
docker exec -it ollama ollama run gemma4:12b-mlx
```

### 3. 在 GPU 容器中執行 Whisper 語音轉文字
您可以利用 `whisper-gpu` 容器內部的 CUDA 環境來進行轉譯。
首次執行前，請在容器內安裝 `uv`（因為此容器是隔離的，您可以透過以下單行指令自動完成安裝與轉譯）：

```bash
docker exec -it whisper-gpu sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=\$HOME/.local/bin:\$PATH && uv run skills/transcribe.py docs/您的目錄/音訊檔案.mp3"
```
這會以 GPU 加速完成轉譯，並在相同的資料夾下產出 `.txt` 檔案。
