<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Stdio mode dành cho MCP client cục bộ khởi chạy `local-shell-mcp` như child process và giao tiếp qua standard input/output.

Đây không phải deployment HTTP công khai. ChatGPT web/app không thể dùng trực tiếp vì ChatGPT không thể tạo process trên máy của bạn.

## Khi nào dùng stdio

Dùng stdio mode khi:

- MCP client hỗ trợ định nghĩa server dựa trên command.
- Client và workspace được điều khiển nằm trên cùng máy.
- Bạn không cần OAuth, HTTPS công khai, reverse proxy hoặc tunnel.
- Bạn muốn client quản lý server lifecycle.

Không dùng stdio mode khi:

- Client là ChatGPT web/app.
- Nhiều remote client cần cùng một server.
- Bạn cần tokenized file download qua HTTP.
- Bạn cần remote-worker join route được phục vụ qua HTTP.

## Lệnh

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Cấu hình MCP client chung thường có dạng:

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

Điều chỉnh schema theo client. Một số client gọi phần này là `servers`, `tools`, `mcpServers` hoặc `contextServers`.

## Khác biệt hành vi so với HTTP mode

| Khu vực | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Không có | `/mcp` |
| OAuth | Không cần | Khuyến nghị cho sử dụng công khai |
| Health endpoint | Không có | `/healthz`, `/readyz` |
| ChatGPT công khai | Không | Có, sau HTTPS |
| Server lifecycle | client khởi chạy process | Bạn quản lý process/runtime |

Ngoài ra tool surface dùng cùng server-side implementation, tùy theo configuration và hỗ trợ của client.

## Ghi chú an toàn

Stdio mode thường chạy trực tiếp trên host với cùng user như MCP client. Hãy dùng workspace root hẹp và tránh truy cập filesystem quá rộng. Giữ full-container mode tắt trừ khi stdio tự chạy trong container hoặc VM có thể bỏ đi.
