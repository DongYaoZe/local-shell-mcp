<!-- i18n-source-sha256: 8c683835be3adb3bf08d9d69b1731f61a39753bf255170fc663cf9456a0df54f -->
# 人機介面

`local-shell-mcp` 在同一個服務 API、工作區、持久終端註冊表、遠端 worker 註冊表和 MCP 稽核日誌之上提供兩種相容的人機介面：

- **Web UI** 是原生瀏覽器儀表板，針對快速檢查執行狀態進行最佳化。
- **OpenTUI** 是完整的終端式應用，既可在瀏覽器中使用，也可作為原生終端命令執行。

兩種模式都不會建立獨立的控制平面。切換介面不會改變已連線機器、Session、job、權限或稽核資料。

## 啟動服務

正常啟動 `local-shell-mcp`：

```bash
local-shell-mcp --mode mcp
```

## ChatGPT Live Workspace

當 ChatGPT 支援渲染 MCP Apps 時，`workspace_open` 會為目前附著的 logical Session 開啟懸浮式協作視圖。Session 持有持久任務狀態；Live Workspace 只負責呈現即時活動和人類控制。因此 App 重連或 ChatGPT/MCP transport 改變都不會重設 Session。

典型交接流程如下：

```text
session_manage(action="start", objective=...)
        -> session_id
... tool work + session_manage(action="report", ...) ...
new agent run
session_manage(action="resume", session_id=..., takeover=true)
        -> inherited progress, Plan, and recent activity
workspace_open()
        -> reconnectable view of that Session
```

`takeover=true` 會取代仍處於 active 狀態的舊 agent run。被取代 run 之後發出的任何工具呼叫都會被拒絕，直到該 agent 明確再次 resume Session。Session 不綁定 machine 或 working directory；一般工具參數仍決定本地/遠端目標和路徑。

可選的 `plan_manage` Plan 會為 Session 啟用 Goal mode。Plan active 且 15 分鐘沒有 agent activity 時，已附著的 Live Workspace 可以要求 ChatGPT 繼續；續跑會先 resume 同一個 `session_id`，並限制為最多 10 次 continuation attempt（無論接受或拒絕）。blocked、completed、cancelled Plan 不會自動續跑；如果 active Plan 的所有 step 都已 completed/skipped，仍可觸發一次用於收尾的 continuation，讓 resumed agent 正式 finish Plan。人類的 pause/resume/cancel 控制修改的是 Session 持有的 Plan，而非暫時 Live Workspace state。

## 瀏覽器介面

開啟：

```text
http://127.0.0.1:8765/ui
```

公開部署則使用設定的 HTTPS origin：

```text
https://your-public-host.example.com/ui
```

瀏覽器介面與 MCP 使用同一套 OAuth 服務和 scope。頁面框架與靜態資源保持公開，以便登入畫面能載入；`/api/ui/*` 與 OpenTUI 終端 WebSocket 仍受保護。存取權杖只儲存在瀏覽器 session storage 中。

### 選擇介面

OAuth 畫面提供兩個入口：

- **Open Web UI**：授權並開啟原生儀表板。
- **Continue to OpenTUI**：授權並開啟終端介面，保留先前的瀏覽器互動方式。

授權後，可透過側邊欄的介面選擇器在 Web UI 與 OpenTUI 之間切換，無需重新登入。暫時切到 OpenTUI 時，當前原生頁面會被記住。

路由可加入書籤：

```text
/ui/#/overview
/ui/#/machines
/ui/#/workloads
/ui/#/activity
/ui/#/console
```

`#/web` 與 `#/dashboard` 是 Overview 的別名；`#/tui` 與 `#/opentui` 是 Console 的別名。

## 原生 Web UI

原生 Web UI 每五秒輪詢現有的人機介面 API，並使用瀏覽器原生控制項而不是終端字元單元進行渲染。只有選擇 OpenTUI 後才會啟動 PTY。

### Overview

Overview 優先顯示最重要的執行資訊：

- Controller 健康狀態與目前 LSM 版本。
- 線上與離線機器數量。
- 活躍的 tracked job 與持久終端工作階段。
- CPU、記憶體、工作區磁碟、load、網路吞吐和 uptime。
- 根據 worker 狀態、資源閾值、失敗 job 與失敗 MCP 呼叫產生的警示。
- 最近由模型發起的 MCP 活動。

### Machines

Machines 列出本機 controller 與已連線的遠端 worker，並顯示狀態、平台、版本、工作目錄、能力及 last-seen 資訊。

### Workloads

Workloads 合併顯示活躍 tracked job 與獨立的持久 shell 工作階段。Web UI 對這些記錄保持唯讀；需要互動式工作階段管理時請使用 OpenTUI。

### Activity

Activity 合併顯示目前警示與近期 MCP 稽核活動。人類輸入的命令與檔案操作不會寫入 MCP 稽核日誌。

## 瀏覽器 OpenTUI

選擇 **OpenTUI** 後，會按需啟動與原生終端啟動器相同的 OpenTUI 應用。瀏覽器 console 保留：

- 經過驗證、透過 WebSocket 傳輸的二進位 PTY。
- 自動終端 resize 與重連退避。
- 使用 OpenTUI 控制項進行滑鼠互動。
- 全螢幕模式與瀏覽器安全的鍵盤快速鍵。
- 行動裝置快速鍵與明確的軟鍵盤控制。
- 透過 xterm.js 支援 SIXEL 與 inline image。

使用者停留在原生 Web UI 模式時，瀏覽器不會建立 OpenTUI PTY。

## 原生 OpenTUI

獨立 release 可執行檔內嵌對應平台的 OpenTUI runtime。只需保留主可執行檔，啟動服務後執行：

```bash
local-shell-mcp tui
```

原生 TUI 不要求人工操作員登入。啟動器會透明地向 loopback API 提供自動產生的本機憑證。該憑證存放在設定的 state directory 中，並使用僅 owner 可存取的權限；即使反向代理從 loopback 連線，也不會取得此 bypass。

原始碼 checkout 在安裝 Bun 相依套件後也可執行 TUI：

```bash
cd ui
bun install --frozen-lockfile
bun run build
cd ..
local-shell-mcp tui
```

只有本機服務使用非預設連接埠時才需要 `--api-base`：

```bash
local-shell-mcp tui --api-base http://127.0.0.1:9876/api/ui
```

## OpenTUI 畫面

### Dashboard

Dashboard 是 OpenTUI 的執行概覽。寬終端會分別顯示節點、workload、警示、activity、系統資訊與趨勢區域；較窄終端會將它們折疊成緊湊摘要，不產生水平捲動。

### Files

Files 是 LSM 原生三欄檔案管理器，可操作本機與遠端機器。它支援建立、編輯、重新命名、複製、移動、貼上、刪除、隱藏檔切換、重新整理、文字預覽、二進位預覽與受限尺寸的圖片縮圖。

### Terminals

Terminals 管理本機與遠端機器上的持久 shell 工作階段。它支援完整命令輸入、raw 互動輸入、工作階段切換、建立與終止、近期輸出，以及可摺疊的 MCP 稽核欄。

### Audit

Audit 讀取有界 JSONL 稽核日誌，並支援 node、operation、event、session、search、time-range 與 sort 篩選，以及記錄詳細資訊檢視。

### Remotes

Remotes 顯示線上與離線遠端 worker、能力、工作目錄及系統中繼資料。它可以建立一次性 join invite、重新命名節點或撤銷其持久身分。

## OpenTUI 導航

原生終端與瀏覽器 console 中，頂部分類列與底部情境操作都可用滑鼠點擊。

| 按鍵 | 操作 |
|---|---|
| `Alt+1` … `Alt+5` | 開啟 Dashboard、Files、Terminals、Remotes 或 Audit。 |
| `F2` … `F6` | 備用分類快速鍵。 |
| `F1` | 開啟鍵盤指南。 |
| `F9` | 重新整理機器清單。 |
| `Alt+Q` | 離開原生 OpenTUI 程序，同時避免觸發瀏覽器保留的 Ctrl 快速鍵。 |

Terminals 使用 `Alt+N` 建立新工作階段、`Alt+W` 終止所選工作階段、`Alt+A` 切換其稽核欄、`Alt+R` 重新整理，並用 `Alt+Left/Right` 切換工作階段。瀏覽器 console 會在瀏覽器層級導覽或選單處理前攔截這些組合鍵。

## 設定

| YAML key | 環境變數 | 預設值 | 用途 |
|---|---|---|---|
| `ui_enabled` | `LOCAL_SHELL_MCP_UI_ENABLED` | `true` | 掛載或停用人機介面。 |
| `ui_path` | `LOCAL_SHELL_MCP_UI_PATH` | `/ui` | MCP 服務上的瀏覽器介面掛載路徑。 |
| `ui_tui_command` | `LOCAL_SHELL_MCP_UI_TUI_COMMAND` | auto | 覆寫原生 OpenTUI 可執行檔解析。 |
| `ui_wallpaper` | `LOCAL_SHELL_MCP_UI_WALLPAPER` | `bing` | 為 OpenTUI 瀏覽器 console 部署保留的桌布設定。 |
| `ui_terminal_idle_timeout_s` | `LOCAL_SHELL_MCP_UI_TERMINAL_IDLE_TIMEOUT_S` | `3600` | 瀏覽器 OpenTUI PTY 閒置達此秒數後關閉；`0` 表示停用逾時。 |
| `ui_terminal_max_sessions` | `LOCAL_SHELL_MCP_UI_TERMINAL_MAX_SESSIONS` | `8` | 瀏覽器 OpenTUI PTY 的最大並行工作階段數。 |

## 打包說明

- Docker 映像包含 Web UI 資源與原生 OpenTUI runtime。
- 獨立可執行檔內嵌 Web UI 資源與壓縮後的平台 OpenTUI runtime。
- Python wheel 包含瀏覽器資源；原生 OpenTUI 需要 release 可執行檔，或安裝了 Bun 相依套件的原始碼 checkout。
- 兩種介面都由與 MCP 相同的程序和連接埠提供，不需要額外 Web 服務。
