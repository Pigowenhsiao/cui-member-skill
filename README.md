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
| `/process <YouTube URL>` | **一鍵完整處理** Steps 1〜5（下載→分類→轉譯→摘要→同步） | YouTube URL |
| `/download <YouTube URL>` | Step 1: 下載音訊與元數據 | YouTube URL |
| `/organize <mp3路徑>` | Step 2: AI 判斷類型與日期，建立目錄並移動檔案 | `.mp3` 檔案路徑 |
| `/transcribe <mp3路徑>` | Step 3: 語音轉文字，產生 `.txt` 文字稿 | `.mp3` 檔案路徑 |
| `/summarize <txt路徑>` | Step 4: 讀取文字稿，輸出繁體中文投資分析報告 `summary.md` | `.txt` 檔案路徑 |
| `/sync` | Step 5: 將生成的會員直播筆記自動同步至 GitHub Gist | （無） |

---

## 前置需求與安裝

> ⚠️ **Mac 版** 與 **Windows 版** 的設定有所不同，請根據您的系統參考下方對應章節。

---

## 🍎 Mac 版設定（適用 Apple Silicon M3 或以上）

### 1. 安裝系統工具

```bash
# 使用 Homebrew 進行安裝
brew install yt-dlp ffmpeg uv
```

### 2. 準備 Cookies 檔案（下載會員限定影片）

要下載會員專屬內容，需要將瀏覽器的 Cookies 傳遞給 yt-dlp。
基於目前的設定，**系統會自動嘗試從您的瀏覽器（預設為 Chrome）讀取 Cookies**，因此通常情況下您**不需手動匯出 Cookies**，即可直接執行腳本下載。

若您使用的是其他瀏覽器，請在 `.env` 檔案中修改 `COOKIES_BROWSER` 變數：
```bash
# .env 檔案
COOKIES_BROWSER=firefox  # 支援 chrome, firefox, edge, safari 等
```

#### 特殊情況：手動匯出 Cookies

只有當自動讀取 Cookies 失敗，或是您基於隱私/環境限制不希望 yt-dlp 直接存取瀏覽器資料時，才需要手動匯出 Cookies。
詳細的 Cookies 取得方式，請參考 [yt-dlp 官方文件說明](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)。

- **Firefox**：使用 [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) 擴充功能
- **Chrome**：使用 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 擴充功能
  - ⚠️ 注意：「Get cookies.txt」（不含 "LOCALLY" 的版本）曾**被舉報為惡意軟體**，請絕對不要安裝。務必使用帶有 "**LOCALLY**" 字樣的版本。

請將匯出的檔案放置於 `./cookies.txt`（根據 `.env` 中的 `COOKIES_PATH` 設定）。
*請注意：Cookies 檔案包含敏感的登入資訊，絕對不要提交（Commit）到 Git 中（已在 `.gitignore` 排除）。*

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
| `GITHUB_TOKEN` | 同步 Gist 專用（需包含 `gist` 權限） | — |
| `GIST_ID` | 同步 Gist 專用（目標 Gist 的 ID） | — |

> ⚠️ **注意 (API 限制)**：當 `WHISPER_MODE` 設定為 `azure`（或 `openai`）時，受限於官方 API 規格，**音訊檔案大小不得超過 25MB**。對於超過此大小的影片（例如長篇直播），請務必切換為 `local` 模式進行轉譯。

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

與 Mac 版本相同，**系統會自動嘗試從您的瀏覽器（預設為 Chrome）讀取 Cookies**，因此您**無需進行手動匯出**即可下載會員影片。

若需指定其他瀏覽器，請在 `.env` 中設定 `COOKIES_BROWSER`（如 `firefox`）。

#### 特殊情況：手動匯出 Cookies

只有當自動讀取失敗時，才需要手動使用擴充功能匯出 `cookies.txt`。
詳細的 Cookies 取得方式，請參考 [yt-dlp 官方文件說明](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)。

- **Firefox**：[cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
- **Chrome**：[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

> ⚠️ **注意換行字元**：若您手動匯出 Cookies 檔案並在 Windows 上使用，請確保換行字元為 **CRLF (`\r\n`)**，否則可能會發生 `HTTP Error 400: Bad Request`。

### 3. 啟動 GPU 容器環境（Docker）

在專案目錄下執行：

```bash
docker-compose up -d
```

這將會啟動支援 NVIDIA GPU 的 `whisper-gpu` 容器。

### 4. 在 GPU 容器內進行 Whisper 轉譯

```bash
docker exec -it whisper-gpu sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=\$HOME/.local/bin:\$PATH && uv run skills/transcribe.py docs/your-dir/audio.mp3"
```

轉譯完成後，會在同一個資料夾內產出 `.txt` 檔案。

### 5. 設定環境變數

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
| `GITHUB_TOKEN` | 同步 Gist 專用（需包含 `gist` 權限） | — |
| `GIST_ID` | 同步 Gist 專用（目標 Gist 的 ID） | — |

> ⚠️ **注意 (API 限制)**：當 `WHISPER_MODE` 設定為 `azure`（或 `openai`）時，受限於官方 API 規格，**音訊檔案大小不得超過 25MB**。對於超過此大小的影片（例如長篇直播），請務必切換為 `local` 模式進行轉譯。

---

## 使用方法 (Workflow)

**最推薦的方式是將 YouTube URL 直接貼給 AI Agent，並讓其依照 `AGENTS.md` 自動執行任務。**

### 手動執行步驟（供參考）

**Step 1: 下載音訊**
```bash
uv run skills/download_audio.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
# 系統將自動讀取 .env 中的 COOKIES_BROWSER 設定（預設為 chrome）
# 若需要，您也可以透過參數強制指定本次要使用的瀏覽器：
uv run skills/download_audio.py --browser firefox "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
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

**Step 5: 同步至 Gist (選擇性)**
```bash
uv run skills/sync_gist.py
```
> 💡 **如何取得 GitHub Token 與 Gist ID？**
> 1. **GitHub Token**：前往 GitHub [Personal Access Tokens (classic)](https://github.com/settings/tokens) 頁面，點擊 `Generate new token (classic)`，填寫名稱並**務必勾選 `gist` 權限**，生成後將其填入 `.env`。
> 2. **Gist ID**：前往 [GitHub Gist](https://gist.github.com/)，隨意建立一個新的 Gist。建立完成後，網址列中 `https://gist.github.com/您的帳號/` 後方的一長串英數代碼即為 `GIST_ID`。

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
