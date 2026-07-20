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
| `/process <YouTube URL>` | **一鍵完整處理** Steps 1〜6（下載→分類→轉譯→摘要→同步） | YouTube URL |
| `/download <YouTube URL>` | Step 1: 下載音訊與元數據 | YouTube URL |
| `/organize <mp3路徑>` | Step 2: AI 判斷類型與日期，建立目錄並移動檔案 | `.mp3` 檔案路徑 |
| `/transcribe <mp3路徑>` | Step 3: 語音轉文字，產生 `.txt` 文字稿 | `.mp3` 檔案路徑 |
| `/summarize <txt路徑>` | Step 4: 讀取文字稿，輸出繁體中文投資分析報告 `summary.md` | `.txt` 檔案路徑 |
| `/sync` | Step 5: 將各分類最新的筆記自動同步至 GitHub Gist（維持單一最新檔案，清理舊檔） | （無） |
| `/archive` | Step 6: 掃描 `./archive` 配下的 Git 專案並同步文件（安全起見需手動 Push） | （無） |

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

## 🪟 Windows 版設定（完全容器化支援 Docker / Podman）

Windows 版本現在採用**完全容器化**架構，不需要在主機上安裝 Python、uv、yt-dlp 或 ffmpeg。只需準備好容器環境即可。

### 1. 安裝必要工具

- 請安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（推薦包含 NVIDIA Container Toolkit 以支援 GPU 加速）。
- （或者）如果不想使用 Docker，也可以安裝 Podman。系統會自動偵測並切換。

### 2. 準備 Cookies 檔案（下載會員限定影片）

由於容器化環境無法直接讀取本機瀏覽器的 Cookies，要下載會員專屬內容，**必須手動匯出 Cookies**。
詳細的 Cookies 取得方式，請參考 [yt-dlp 官方文件說明](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)。

- **Firefox**：使用 [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) 擴充功能
- **Chrome**：使用 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 擴充功能

請將匯出的檔案命名為 `cookies.txt`，並放置於專案根目錄下。
> ⚠️ **注意換行字元**：請確保換行字元為 **CRLF (`\r\n`)** 或 LF，格式錯誤可能會發生 `HTTP Error 400: Bad Request`。

### 3. 啟動容器環境 (Docker / Podman)

在專案目錄下執行：

```bash
# 預設：啟動支援 NVIDIA GPU 的容器
docker compose up -d

# 若您的電腦沒有 NVIDIA GPU，請改用 CPU 版本啟動：
docker compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

這將會啟動包含 yt-dlp, ffmpeg, uv 等所有必備工具的 `cui-tools` 容器。

### 4. 在容器內執行腳本

容器啟動後，所有的指令皆透過 `docker exec` (或 `podman exec`) 在 `cui-tools` 容器內執行：

```bash
docker exec cui-tools uv run skills/transcribe.py docs/your-dir/audio.mp3
```

### 5. 設定環境變數

```bash
copy .env.example .env
```

可以在 `.env` 中設定的主要參數：

| 變數名稱 | 說明 |
|--------|------|
| `WHISPER_MODE` | `local`（Docker GPU/CPU）/ `openai` / `azure` | `local` |
| `CONTAINER_RUNTIME`| 指定使用的容器工具，預設留空系統自動偵測 | `docker` |
| `COOKIES_PATH` | Cookies 檔案的存放路徑 | `./cookies.txt` |
| `OPENAI_API_KEY` | 使用 OpenAI API 模式時為必填 | — |
| `GITHUB_TOKEN` | 同步 Gist 專用（需包含 `gist` 權限） | — |
| `GIST_ID` | 同步 Gist 專用（目標 Gist 的 ID） | — |

> ⚠️ **注意 (API 限制)**：當 `WHISPER_MODE` 設定為 `azure`（或 `openai`）時，受限於官方 API 規格，**音訊檔案大小不得超過 25MB**。對於超過此大小的影片（例如長篇直播），請務必切換為 `local` 模式進行轉譯。

---

## 使用方法 (Workflow)

**最推薦的方式是將 YouTube URL 直接貼給 AI Agent，並讓其依照 `AGENTS.md` 自動執行任務。**

### 手動執行步驟（供參考）

> **⚠️ 注意**：以下指令以 Mac 版 (`uv run`) 為例。若您使用 Windows 版，請在所有 `uv run` 指令前方加上 `docker exec cui-tools` (或 `podman exec cui-tools`)。

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
將各分類的最新分析報告以 `分類名稱.md`（例如：`會員直播.md`）的格式上傳至 Gist，自動覆蓋並清理舊檔以維持頁面整潔。
```bash
uv run skills/sync_gist.py
```
> 💡 **如何取得 GitHub Token 與 Gist ID？**
> 1. **GitHub Token**：前往 GitHub [Personal Access Tokens (classic)](https://github.com/settings/tokens) 頁面，點擊 `Generate new token (classic)`，填寫名稱並**務必勾選 `gist` 權限**，生成後將其填入 `.env`。
> 2. **Gist ID**：前往 [GitHub Gist](https://gist.github.com/)，隨意建立一個新的 Gist。建立完成後，網址列中 `https://gist.github.com/您的帳號/` 後方的一長串英數代碼即為 `GIST_ID`。

**Step 6: アーカイブ同期 (Sync to Archive)**
若在 `./archive` 目錄下存在您的 Git 存檔專案，此腳本會自動將最新的 `docs/**/*.md` 拷貝至專案內，並自動執行 `git add` 與 `git commit`。
⚠️ **安全性提示**：為避免在 Docker 容器內掛載 SSH 私鑰帶來潛在的資安風險，本腳本**不會**自動執行 `git push`。請於腳本執行完畢後，手動在主機端推送至 GitHub。
```bash
uv run skills/sync_archive.py
```

---

## 專案結構

cui-member-skill/
├── AGENTS.md                  # 給 AI Agent 閱讀的自動化操作手冊
├── README.md                  # 本文件
├── .env.example               # 環境變數設定範本
├── .gitignore
├── Dockerfile                 # Windows 容器化影像定義檔
├── docker-compose.yml         # Windows NVIDIA GPU 專用的 Docker 設定檔
├── docker-compose.cpu.yml     # Windows CPU 專用的 Docker 設定檔
├── skills/                    # 自動化技能腳本
│   ├── download_audio.py      # 音訊與中繼數據的下載
│   ├── transcribe.py          # 語音轉文字（支援 Local/OpenAI/Azure，自動判別 CPU/GPU）
│   ├── sync_gist.py           # 同步 Gist 的腳本
│   ├── sync_archive.py        # 本地 Git 專案同步（歸檔）腳本
│   └── prompts/               # 各階段專屬的 Agent 提示詞與操作說明
│       ├── process.prompt.md
│       ├── download.prompt.md
│       ├── organize.prompt.md
│       ├── transcribe.prompt.md
│       ├── summarize.prompt.md
│       └── summarize.md       # 給 LLM 的分析提示詞範本
├── docs/                      # 輸出目錄（按影片類型/日期分類存放）
└── ./
    └── cookies.txt            # Cookies 檔案（已在 Git 中忽略）

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
