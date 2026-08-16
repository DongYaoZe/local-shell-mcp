<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Lựa chọn runtime và mô hình deployment

`local-shell-mcp` có hai quyết định độc lập:

1. **Runtime**: process server chạy như thế nào và kiểm soát workspace nào.
2. **Client connection**: ChatGPT hoặc MCP client khác truy cập server đó như thế nào.

Đừng xem ChatGPT là phương thức deployment. ChatGPT là client. Docker, VS Code extension, release binaries, cài đặt Python và stdio mode là lựa chọn runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Một setup công khai thường gặp:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Setup MCP client cục bộ có thể đơn giản hơn:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Ma trận lựa chọn runtime

| Runtime | Phù hợp nhất | Ranh giới cách ly | Nguồn toolchain | Truy cập ChatGPT công khai | Trang |
|---|---|---|---|---|---|
| Docker Compose | Phần lớn coding-agent workloads và workspaces tái lập | Container | Project image chứa default toolchain rộng | Thêm HTTPS proxy hoặc tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Deployment công khai một stack với Cloudflare Tunnel | Container | Project image | Tích hợp trong profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Start/stop server từ editor workspace | Thường là host process | Host tools cộng executable cấu hình | Thêm HTTPS tunnel/proxy ngoài cho ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Host hoặc VM không có Docker | Host or VM | Host tools cộng executable cấu hình | Thêm HTTPS proxy hoặc tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Dùng Python-native, debugging, development | Host virtualenv or VM | Python package cộng host tools | Thêm HTTPS proxy hoặc tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP client cục bộ spawn process trực tiếp | Client process boundary | Host tools cộng executable cấu hình | Không dùng được với ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Ma trận kết nối client

| Client path | Cần HTTPS công khai | Dùng `/mcp` | Cần OAuth | Runtime điển hình |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Có | Có | Có khi dùng công khai | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Không | Không | Không | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Thường không ở localhost; có qua mạng | Có | Khuyến nghị ngoài localhost | Any HTTP runtime |
| VS Code extension helper flow | Chỉ khi ChatGPT cần connect | Có khi copy URL ChatGPT | Khuyến nghị cho ChatGPT | VS Code-launched runtime |

Xem [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Mỗi runtime kiểm soát gì

Mỗi runtime khởi chạy cùng server code và cung cấp cùng các family MCP tools khi được bật:

- Shell và persistent shell sessions.
- Filesystem, search và patch tools.
- Git operations.
- Browser automation qua Playwright.
- Audit log và task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle và machine-routed tools.

Khác biệt không nằm ở abstract API mà ở **operating environment** phía sau.

| Câu hỏi | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Command chạy ở đâu? | Trong container | Thường trên host workspace | Trong host hoặc VM process environment |
| Default workspace? | Mounted `/workspace` | Folder VS Code hiện tại hoặc path cấu hình | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser cài sẵn? | Có, khá đầy đủ | Chỉ nếu đã cài trên host | Chỉ nếu đã cài trên host |
| Reset dễ không? | Tạo lại container và workspace volume | Phụ thuộc workspace | Phụ thuộc host/VM |
| Phù hợp arbitrary package install? | Có nếu disposable | Rủi ro hơn trên host | Rủi ro hơn ngoài VM |

## Lựa chọn khuyến nghị

Dùng **Docker Compose** trước trừ khi có lý do khác. Nó cung cấp safety boundary rõ nhất và default toolchain đầy đủ nhất.

Dùng **VS Code extension** khi workflow bắt đầu từ editor và cần local launcher. Nó vẫn là runtime. Bản thân nó không làm server truy cập được từ ChatGPT; thêm tunnel hoặc reverse proxy cho ChatGPT web/app.

Dùng **standalone binary** khi Docker không khả dụng nhưng VM, container host hoặc dedicated user account đã tạo boundary.

Dùng **`pipx` hoặc source install** để development/debugging `local-shell-mcp` hoặc khi Python-based environment dễ duy trì hơn.

Chỉ dùng **stdio mode** cho MCP client cục bộ có thể spawn server process. Nó không phải public deployment và không dùng trực tiếp được từ ChatGPT web/app.

## Quy tắc public endpoint

Với HTTP MCP client như ChatGPT, MCP endpoint là:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` chỉ là origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Không thêm `/mcp` vào `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Trang runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Trang client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
