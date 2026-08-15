# 工具參考

本頁概述 `local-shell-mcp` 目前公開的 MCP 工具。英文參考頁由實際 MCP Schema 自動生成，包含每個參數的類型和預設值。

公開工具返回包含 `ok`、`message`、`data` 的結構化結果；`workspace_open` 返回用於渲染 MCP App 的模型可見狀態。多數執行、檔案和瀏覽器工具都接受可選的 `machine` 參數：省略時在控制端執行，指定時在對應遠端 worker 執行，並額外要求 `remote:use` 權限。

Git 不再擁有專用 MCP 工具。請透過 `run_shell` 執行標準 Git CLI，例如 `git status --short --branch`、`git diff`、`git commit` 和 `git push`。

## 工具分組

### Live Workspace

`workspace_open`


### 環境、Skills 與任務狀態

`environment_get`、`skill_list`、`skill_load`、`skill_read`、`secret_scan`、`session_manage`、`plan_manage`、`audit_tail`

`environment_get` 已包含執行版本、Python、平台、可執行檔、工作區、權限策略和基礎探測資訊，因此不再單獨暴露 `version_info`。

### Shell 與長期任務

`run_shell`、`run_python`、`shell_start`、`shell_send`、`shell_read`、`shell_stop`、`shell_list`、`job_start`、`job_list`、`job_tail`、`job_stop`、`job_retry`

- 短期、非互動命令使用 `run_shell`。
- 需要互動的終端、REPL、TUI 使用 `shell_*`。
- 需要可追蹤、停止和重試的長期任務使用 `job_*`。

### 檔案、搜尋與傳輸

`file_list`、`file_tree`、`file_glob`、`file_grep`、`file_read`、`image_view`、`file_write`、`file_edit`、`file_delete`、`file_patch`、`remote_transfer`

- `file_read.path` 可以是單一路徑，也可以是路徑陣列。
- `file_edit.edits` 接受一個或多個精確替換項，不再區分單次與批次編輯工具。
- `remote_transfer` 自動判斷來源是檔案還是目錄，並立即建立一個可追蹤的傳輸 job，支援控制端到 worker、worker 到控制端以及 worker 到 worker。使用 `job_list`、`job_tail`、`job_stop` 和 `job_retry` 查看、停止或重試；worker 到控制端的上傳使用可續傳的原始二進位分塊。`source_machine` 或 `destination_machine` 至少指定一個。

### 瀏覽器自動化

`browser_session`、`browser_snapshot`、`browser_act`、`browser_run_script`

- 一般頁面檢查、文字讀取和截圖優先使用 `browser_session`、`browser_snapshot` 與 `browser_act`。
- JavaScript 求值、自訂截圖/PDF 和複雜流程由 `browser_run_script` 執行完整 Playwright 腳本。
- 瀏覽器安裝使用一般 shell 命令，不再長期占用獨立工具入口。

### 檔案下載連結

`link_create`、`link_list`、`link_revoke`

連結使用高熵 bearer token，並支援 TTL、下載次數限制和主動撤銷。

### 遠端 worker 管理

`remote_manage`

只有 worker 管理繼續使用 `remote_*` 名稱。實際執行使用一般工具及其 `machine` 參數。

## 常用流程

| 需求 | 建議工具 |
|---|---|
| 檢查環境 | `environment_get` → `file_tree` → `file_read` |
| Git 操作 | `run_shell` 執行標準 Git CLI |
| 精確修改檔案 | `file_read` → `file_edit` / `file_patch` → 測試與 `git diff` |
| 長時間任務 | `job_start` → `job_tail` → `job_stop` / `job_retry` |
| 遠端執行 | 同一工具增加 `machine` |
| 跨機器傳輸 | `remote_transfer` |
| 瀏覽器證據 | `browser_snapshot` / `browser_run_script` |
