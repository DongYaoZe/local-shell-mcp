<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# 審計日誌

`local-shell-mcp` 會寫入結構化審計記錄，幫助還原已連接客戶端做過什麼。

默認路徑：

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## 記錄內容

審計記錄覆蓋這些事件：

- 工具調用開始和結束。
- 命令執行元數據。
- 超時和已處理錯誤。
- 遠程 worker 註冊和任務活動。
- 文件鏈接創建和撤銷。
- 適用時的認證相關事件。

服務能識別的敏感參數會被脫敏。

## 讀取日誌

使用 MCP 工具：

```text
audit_tail
```

也可以直接查看：

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## 運維用途

審計日誌主要用於：

- 複查修改文件的命令。
- 檢查是否使用過遠程 worker。
- 調試意外失敗。
- 發現文件鏈接的意外暴露。
- 在公開部署配置錯誤後支持事件響應。

## 保留策略

作用中的 `audit.jsonl` 預設由 `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` 限制為 20 MB。執行保留維護時，較舊記錄會移入 `audit-archive/*.jsonl.zst` 的自包含 Zstandard 封存，而不是直接丟棄；外置的大型 audit payload 也會先寫入封存。

壓縮封存由 `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` 另行限制，預設為 512 MB；超過後會先刪除最舊封存。設為 `0` 可停用長期壓縮保留。近期查詢只讀取熱日誌，需要歷史記錄時才查詢封存。

## 限制

審計日誌不是沙箱。它能提升可追蹤性，但不能阻止已連接模型在配置權限範圍內執行操作。
