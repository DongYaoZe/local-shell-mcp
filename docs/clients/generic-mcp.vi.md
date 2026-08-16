<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client dùng chung

`local-shell-mcp` có thể được dùng bởi ChatGPT và các MCP client khác. Client quyết định kết nối qua HTTP hay tự khởi chạy server qua stdio.

## MCP client HTTP

Dùng HTTP mode khi server đã chạy:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint cục bộ:

```text
http://127.0.0.1:8765/mcp
```

Endpoint mạng:

```text
https://your-public-host.example.com/mcp
```

Dùng OAuth cho mọi endpoint có thể truy cập ngoài localhost đáng tin cậy.

## MCP client stdio

Dùng stdio mode khi client tự khởi chạy tiến trình server:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Dạng cấu hình client điển hình:

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

Schema của client khác nhau. Một số gọi phần này là `mcpServers`; số khác dùng tên khác.

## Kiểm tra an toàn đầu tiên

Với client mới kết nối, bắt đầu bằng:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Sau đó chạy một tác vụ có giới hạn với quy tắc chỉnh sửa, kiểm thử và Git rõ ràng.
