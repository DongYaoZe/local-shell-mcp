<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# 通用 MCP 客戶端

`local-shell-mcp` 可供 ChatGPT 使用，也可供其它 MCP 客戶端使用。客戶端決定是通過 HTTP 連接，還是通過 stdio 啓動服務。

## HTTP MCP 客戶端

當服務已經在運行時，使用 HTTP 模式：

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

本地端點：

```text
http://127.0.0.1:8765/mcp
```

網絡端點：

```text
https://your-public-host.example.com/mcp
```

任何超出可信 localhost 範圍可訪問的端點都應使用 OAuth。

## Stdio MCP 客戶端

當客戶端自己啓動服務進程時，使用 stdio 模式：

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

典型客戶端配置結構：

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

不同客戶端 schema 不完全相同。有些叫 `mcpServers`，也有些使用其它名稱。

## 第一次安全檢查

新客戶端連接後，先執行：

```text
調用 environment_get，然後對工作區根目錄調用 file_tree。暫時不要修改文件。
```

之後再運行帶有明確編輯、測試和 Git 規則的有邊界任務。
