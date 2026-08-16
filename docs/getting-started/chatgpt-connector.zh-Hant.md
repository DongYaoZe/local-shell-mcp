# ChatGPT 連接器

本頁說明如何把 ChatGPT 作爲客戶端接入。它不負責選擇運行時。使用本頁前，先通過 Docker、VS Code 擴展、獨立二進制或 Python 安裝方式啓動 `local-shell-mcp` 服務。

`local-shell-mcp` 面向 ChatGPT Developer Mode 和完整 MCP 客戶端設計。MCP 端點直接暴露標準的 LSM 工具面。

## 運行時前置條件

先選擇並啓動一個運行時：

| 運行時 | 頁面 |
|---|---|
| Docker Compose | [Docker Compose 運行時](../installation/docker.md) |
| VS Code 擴展 | [VS Code 擴展運行時](../installation/vscode-extension.md) |
| 獨立二進制 | [獨立二進制運行時](../installation/binary.md) |
| Python / pipx / 源碼 | [Python 運行時](../installation/python.md) |

然後通過 ChatGPT 可訪問的網絡路徑暴露這個運行時。網絡入口與反向代理要求見 [網絡連通性](../clients/connectivity.md)。

## 公共 URL

ChatGPT 必須通過 HTTPS 訪問服務。MCP 端點是：

```text
https://your-public-host.example.com/mcp
```

確保 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 只填寫公開源站地址：

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

不要在 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 後面追加 `/mcp`。

## OAuth 設置

公開部署建議使用以下配置：

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

訪問令牌默認不會自動過期，因爲較長的編程會話可能超過短令牌壽命。需要撤銷訪問時，可以輪換 JWT secret，或使用全新的狀態重新部署。

## 添加連接器

1. 打開 ChatGPT 的連接器設置或 Developer Mode 的 MCP 設置。
2. 添加自定義 MCP 服務器。
3. 輸入 MCP URL：`https://your-public-host.example.com/mcp`。
4. 完成 OAuth 授權。
5. 審覈並批准工具列表。

## Live Workspace MCP App

支援 MCP Apps 的 ChatGPT 客戶端可以渲染 `local-shell-mcp` 的互動式執行工作區。需要即時觀察或人機協作時，只需讓 ChatGPT 為目前任務開啟一次 Live Workspace；此後 App 會自行重連，不需要反覆調用 `workspace_open`。

Live Workspace 只顯示可觀察的執行狀態和共享資源，不顯示模型的私有推理過程：

- **Activity**：顯示 MCP 工具的開始、完成、失敗以及人類操作。
- **Terminal**：連接現有持久 shell 後端，並即時顯示 PTY 輸出。
- **Files**：瀏覽、預覽、編輯、新建和刪除本地或遠端工作區文件。
- **Diff**：顯示 Git 已暫存和未暫存修改，並可把目前 diff 發回 ChatGPT 審查。
- **Jobs**：顯示託管 job 和持久 session。
- **Remotes**：顯示遠端 worker；啓用遠端支援時可建立邀請、重新命名或撤銷 worker。
- **Audit**：查看最近的結構化 MCP 稽覈記錄。

Live Workspace 始終採用協作模式：ChatGPT 與人類可以並行修改同一個工作區。宿主支援時預設以懸浮窗（PiP）開啟，並可在懸浮窗與全螢幕之間來回切換；不再提供 Observe / Take over 狀態。

Files、Diff、Audit 和 Activity 視圖可以通過 MCP Apps bridge 把選中的操作上下文發送到下一輪模型上下文。這些內容屬於顯式共享的上下文；UI 不會暴露或嘗試重建模型的私有推理。

### 網絡與安全

爲了讓終端和事件流保持低延遲，渲染後的 MCP App 會從 sandbox 直接連接到配置的服務源站。因此，`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 必須是 ChatGPT 瀏覽器可以訪問的 HTTPS 源站地址。MCP 端點仍然是 `https://your-public-host.example.com/mcp`。

打開工作區時會簽發隨機、短生命週期的 Live Workspace bearer token。該 token 只放在供渲染 App 使用的 MCP result metadata 中，不進入模型可見的 structured content，並且只會被 human/live UI API 接受。App 使用同一個 `live_id` 自動重新附著時會重用目前憑據，避免重連中的視圖互相使 token 失效；同時會攜帶目前邏輯 `session_id`，因此即使記憶體中的 Live Workspace 狀態遺失，也能恢復到持久 Session。明確再次調用 `workspace_open` 時仍會輪換 token。嵌入式 App 不使用瀏覽器 cookie 或環境中的隱式憑據。

不支援 MCP Apps 的客戶端可以忽略這些 UI metadata。所有普通 MCP 數據工具仍然可用，行爲保持不變。

## 第一次提示詞

```text
使用 local-shell-mcp。先調用 environment_get，然後列出工作區根目錄。暫時不要修改文件。
```

這個提示只驗證連通性，不會主動修改文件。

## 推薦操作規則

給模型明確邊界：

- 除非另有說明，只在 `/workspace` 內工作。
- 提交前先運行測試。
- 推送前使用 `secret_scan`。
- 只對可以分享的文件使用 `link_create`。
- 長時間進程優先使用持久 shell session。
- 彙總所有修改過文件的命令。

## 工具發現問題

如果 ChatGPT 能完成認證，但沒有顯示預期工具：

- 確認端點以 `/mcp` 結尾。
- 檢查 `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`。
- 檢查反向代理請求頭與請求體大小限制。
- 查看 `docker compose logs --tail=200 local-shell-mcp`。
- 確認服務運行在 `mcp` 或 `both` 模式。

## 安全說明

公開部署應保持 OAuth 開啓。不要在公網暴露未認證的完整 MCP 工具。每個被批准的工具都應視爲已接入模型實際權限的一部分。
