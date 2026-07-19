# CUI Member Skill

本專案提供了一套自動化工具與工作流（Skills），專為 YouTube 頻道 **[小翠時政財經](https://www.youtube.com/@cui_news)** 的付費會員設計，旨在將會員限定影片的音訊下載、轉譯為文字，並透過 AI Agent（如 Claude、GitHub Copilot、Codex 或 Antigravity）進行重點摘要與投資分析整理。

## 專案設計理念

- **AI Agent 優先 (Agent-centric)**：功能被封裝為一系列的 Scripts (Skills)，設計初衷是交由 AI Agent 閱讀 `AGENTS.md` 後自動呼叫與執行，而非完全依賴人類手動輸入指令。
- **環境隔離**：所有 Python 腳本皆使用 `uv` 管理內聯依賴（Inline dependencies），確保不污染系統全域環境。
- **靈活的模型切換**：文字轉譯功能（Whisper）支援本地端運算與雲端 API（OpenAI, Azure）。詳細規格因 OS 不同，請見下方各平台設定說明。

---

## 斜線指令（Slash Commands）一覽

將以下指令直接貼給 AI Agent（如本聊天視窗），Agent 將自動完成對應步驟。

| 指令 | 功能 | 必要輸入 |
|------|------|----------|
| `/process <YouTube URL>` | **一鍵完整處理** Steps 1〜4（下載→分類→轉譯→摘要） | YouTube URL |
| `/download <YouTube URL>` | Step 1: 下載音訊與元數據 | YouTube URL |
| `/organize <mp3路徑>` | Step 2: AI 判斷類型與日期，建立目錄並移動檔案 | `.mp3` 檔案路徑 |
| `/transcribe <mp3路徑>` | Step 3: 語音轉文字，產生 `.txt` 文字稿 | `.mp3` 檔案路徑 |
| `/summarize <txt路徑>` | Step 4: 讀取文字稿，輸出繁體中文投資分析報告 `summary.md` | `.txt` 檔案路徑 |

---

## 前置需求與安裝

> ⚠️ **Mac 版** 與 **Windows 版** 的設定有所不同，請根據您的系統參考下方對應章節。

---

## 🍎 Mac 版設定（適用 Apple Silicon / Intel）

### 1. 安裝系統工具

```bash
# 使用 Homebrew 進行安裝
brew install yt-dlp ffmpeg uv
```

### 2. 準備 Cookies 檔案（下載會員限定影片）

要下載會員專屬內容，需要將瀏覽器的 Cookies 傳遞給 yt-dlp。

#### 方法 A：讓 yt-dlp 自動讀取瀏覽器 Cookies（推薦）

yt-dlp 可以直接從瀏覽器中讀取 Cookies。

```bash
# Firefox 的情況
yt-dlp --cookies-from-browser firefox "https://www.youtube.com/..."

# Chrome 的情況
yt-dlp --cookies-from-browser chrome "https://www.youtube.com/..."
```

*(註：本專案的 `skills/download_audio.py` 已支援透過 `--browser` 參數直接呼叫此功能，例如 `--browser chrome`。)*

#### 方法 B：使用瀏覽器擴充功能手動匯出

- **Firefox**：使用 [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) 擴充功能
- **Chrome**：使用 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 擴充功能
  - ⚠️ 注意：「Get cookies.txt」（不含 "LOCALLY" 的版本）曾**被舉報為惡意軟體**，請絕對不要安裝。務必使用帶有 "**LOCALLY**" 字樣的版本。

請將匯出的檔案放置於 `./cookies.txt`。

#### 關於 Cookies 檔案的重要注意事項

根據 yt-dlp 官方 FAQ 說明：

- Cookies 檔案必須為 **Mozilla/Netscape 格式**。
- 檔案的第一行必須以 `# HTTP Cookie File` 或 `# Netscape HTTP Cookie File` 開頭。
- **換行字元** 在 macOS/Linux 上請務必使用 **LF (`\n`)**（Windows 則為 CRLF `\r\n`）。若換行字元不正確，可能會導致 `HTTP Error 400: Bad Request`。
- 該檔案包含了**敏感的登入資訊**，**請絕對不要將其提交（Commit）到 Git 中**（已在 `.gitignore` 中設定排除）。

### 3. 設定環境變數

```bash
cp .env.example .env
```

可以在 `.env` 中設定的主要參數：

| 變數名稱 | 說明 | 預設值 |
|--------|------|-----------|
| `WHISPER_MODE` | 轉譯模式（`local` / `openai` / `azure`） | `local` |
| `WHISPER_MODEL` | 本地端模式時的模型名稱 | `mlx-community/whisper-medium-mlx-8bit` |
| `COOKIES_PATH` | Cookies 檔案的存放路徑 | `./cookies.txt` |
| `COOKIES_BROWSER`| 預設從指定瀏覽器自動讀取 Cookies（如 `firefox`, `chrome`）| `chrome` |
| `OPENAI_API_KEY` | 使用 OpenAI API 模式時為必填 | — |

### 4. 關於 Mac 的本地端轉譯模型

在 Mac（Apple Silicon）上，可以利用 **MLX 框架** 進行高速轉譯。

| 模型 | 精準度 | 處理時間預估 | 推薦用途 |
|--------|------|----------------|----------|
| `mlx-community/whisper-medium-mlx-8bit` | 普通至良好 | **預設**。30分鐘影片約需數分鐘 | 日常一般用途 |
| `mlx-community/whisper-large-v3-mlx` | 最高精準度 | **可能需要 30 分鐘以上** | 僅在極需高精準度時使用 |

> ⚠️ `whisper-large-v3-mlx` 雖然精準度高，但對於長度超過 30 分鐘的影片，**轉譯過程可能會耗時超過 30 分鐘**，請在時間充裕時再使用。

若要更換模型，請編輯 `.env` 檔案：

```bash
# .env
WHISPER_MODEL=mlx-community/whisper-large-v3-mlx
```

對於非 Apple Silicon 的 Mac（Intel Mac），系統將自動降級使用 CPU 版本的 `faster-whisper`（預設為 medium 模型）。

---

## 🪟 Windows 版設定（推薦使用 NVIDIA GPU / CUDA）

### 1. 安裝必要工具

- 請安裝 [WSL2](https://learn.microsoft.com/zh-tw/windows/wsl/install) 與 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（包含 NVIDIA Container Toolkit）。
- 請安裝 `yt-dlp` 與 `ffmpeg`，並將執行檔放置於 `C:\Users\<使用者名稱>\bin` 等目錄中，同時**將其加入環境變數 PATH 中**。

```powershell
# 使用 winget 進行安裝（在 PowerShell 中執行）
winget install yt-dlp ffmpeg
```

### 2. 準備 Cookies 檔案（下載會員限定影片）

#### 方法 A：讓 yt-dlp 自動讀取瀏覽器 Cookies（推薦）

在 PowerShell 中執行：

```powershell
# Firefox 的情況
yt-dlp --cookies-from-browser firefox "https://www.youtube.com/..."

# Chrome 的情況
yt-dlp --cookies-from-browser chrome "https://www.youtube.com/..."
```

> **注意**：這項指令會讀取該瀏覽器中**所有網站**的 Cookie。若有匯出成檔案，**請絕對不要將其提交到 Git 中**（已在 `.gitignore` 設定排除）。

#### 方法 B：使用瀏覽器擴充功能手動匯出

- **Firefox**：使用 [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) 擴充功能
- **Chrome**：使用 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 擴充功能
  - ⚠️ 注意：「Get cookies.txt」（不含 "LOCALLY" 的版本）曾**被舉報為惡意軟體**，請絕對不要安裝。

#### 注意 Cookies 檔案的換行字元

在 Windows 上使用 Cookies 檔案時，請確保換行字元為 **CRLF (`\r\n`)**。如果僅有 LF，可能會發生 `HTTP Error 400: Bad Request` 的錯誤。

### 3. 啟動 GPU 容器環境（Docker）

在專案目錄下執行：

```bash
docker-compose up -d
```

這將會啟動支援 NVIDIA GPU 的 `ollama` 與 `whisper-gpu` 容器。

### 4. 下載本地端 LLM 模型（Ollama）

```bash
docker exec -it ollama ollama run gemma4:12b-mlx
```

### 5. 在 GPU 容器內進行 Whisper 轉譯

```bash
docker exec -it whisper-gpu sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=\$HOME/.local/bin:\$PATH && uv run skills/transcribe.py docs/your-dir/audio.mp3"
```

轉譯完成後，會在同一個資料夾內產出 `.txt` 檔案。

### 6. 設定環境變數

```bash
copy .env.example .env
```

可以在 `.env` 中設定的主要參數：

| 變數名稱 | 說明 |
|--------|------|
| `WHISPER_MODE` | `local`（Docker GPU）/ `openai` / `azure` | `local` |
| `COOKIES_PATH` | Cookies 檔案的存放路徑 | `./cookies.txt` |
| `COOKIES_BROWSER`| 預設從指定瀏覽器自動讀取 Cookies（如 `firefox`, `chrome`）| `chrome` |
| `OPENAI_API_KEY` | 使用 OpenAI API 模式時為必填 | — |

---

## 使用方法 (Workflow)

**最推薦的方式是將 YouTube URL 直接貼給 AI Agent，並讓其依照 `AGENTS.md` 自動執行任務。**

### 手動執行步驟（供參考）

**Step 1: 下載音訊**
```bash
uv run skills/download_audio.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
# 若要自動讀取瀏覽器 Cookie
uv run skills/download_audio.py --browser chrome "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

**Step 2: 建立分類目錄並移動檔案**（交由 AI Agent 自動判斷）
```
./docs/<VideoType>/<Date>/  例如: ./docs/會員直播/20260717/
```

**Step 3: 語音轉文字**
```bash
uv run skills/transcribe.py "./docs/會員直播/20260717/audio_file.mp3"
```

**Step 4: 摘要與分析**
依照 `skills/prompts/summarize.md` 的提示詞，讓 AI Agent 讀取 `.txt` 並生成 `summary.md` 報告。

---

## 專案結構

```
cui-member-skill/
├── AGENTS.md                  # 給 AI Agent 閱讀的自動化操作手冊
├── README.md                  # 本文件
├── .env.example               # 環境變數設定範本
├── .gitignore
├── docker-compose.yml         # Windows NVIDIA GPU 專用的 Docker 設定檔
├── skills/                    # 自動化技能腳本
│   ├── download_audio.py      # 音訊與中繼數據的下載
│   ├── transcribe.py          # 語音轉文字（支援 Local/OpenAI/Azure，自動判別 CPU/GPU）
│   └── prompts/
│       └── summarize.md       # 給 LLM 的分析提示詞範本
├── docs/                      # 輸出目錄（按影片類型/日期分類存放）
└── ./
    └── cookies.txt            # Cookies 檔案（已在 Git 中忽略）
```
