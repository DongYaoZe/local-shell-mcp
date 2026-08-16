<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Trình kết nối ChatGPT

Trang này nói về ChatGPT như một kết nối client. Nó không chọn runtime. Trước khi dùng, hãy chạy server bằng Docker, VS Code extension, binary hoặc cài đặt Python.

`local-shell-mcp` được thiết kế cho ChatGPT Developer Mode và các MCP client đầy đủ. MCP endpoint trực tiếp cung cấp tool surface LSM thông thường.

## Điều kiện runtime

Trước tiên chọn và khởi động một runtime:

| Runtime | Trang |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Sau đó công khai runtime đó qua đường mạng mà ChatGPT có thể truy cập. Xem [network connectivity](../clients/connectivity.md).

## URL công khai

ChatGPT phải truy cập server qua HTTPS. MCP endpoint là:

```text
https://your-public-host.example.com/mcp
```

Đảm bảo `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` khớp public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Không đưa `/mcp` vào `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Thiết lập OAuth

Cấu hình công khai khuyến nghị:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access token mặc định không hết hạn vì coding session dài có thể vượt quá lifetime token ngắn. Khi cần, revoke quyền bằng cách rotate JWT secret hoặc redeploy với state mới.

## Thêm connector

1. Mở cài đặt connector hoặc Developer Mode MCP của ChatGPT.
2. Thêm custom MCP server.
3. Nhập MCP URL: `https://your-public-host.example.com/mcp`.
4. Hoàn tất OAuth.
5. Phê duyệt tool surface.

## Live Workspace MCP App

Client ChatGPT hỗ trợ MCP Apps có thể render `local-shell-mcp` như execution workspace tương tác. Yêu cầu ChatGPT mở Live Workspace một lần khi cần quan sát real-time hoặc cộng tác với con người; sau đó app tự reconnect thay vì gọi `workspace_open` lặp lại.

Live Workspace được tách có chủ ý khỏi reasoning của model. Nó hiển thị execution state có thể quan sát và resources dùng chung:

- **Activity** hiển thị MCP tool start, completion, failure và hành động của con người.
- **Terminal** gắn vào backend persistent shell hiện có với live PTY output.
- **Files** duyệt, preview, edit, create và delete file workspace local/remote.
- **Diff** hiển thị Git changes staged/unstaged và có thể gửi current diff lại ChatGPT để review.
- **Jobs** hiển thị managed jobs và persistent sessions.
- **Remotes** hiển thị workers và cung cấp invite, rename, revoke khi remote support bật.
- **Audit** hiển thị structured MCP audit records gần đây.

Live Workspace luôn collaborative: ChatGPT và con người có thể cùng lúc sửa một workspace. Nó mở dạng floating PiP-style window khi host hỗ trợ và chuyển được giữa fullscreen và windowed. Không có state observe/takeover riêng.

Các view files, diff, audit và activity có thể gửi operational context đã chọn tới model turn tiếp theo qua MCP Apps bridge. Đây là context được chia sẻ rõ ràng; UI không làm lộ hoặc tái tạo private model reasoning.

### Mạng và bảo mật

MCP App đã render kết nối trực tiếp từ sandbox tới service origin đã cấu hình để có terminal/event traffic độ trễ thấp. Vì vậy `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` phải là HTTPS origin mà browser ChatGPT truy cập được. MCP endpoint vẫn là `https://your-public-host.example.com/mcp`.

Khi mở workspace, hệ thống phát hành một Live Workspace bearer token ngẫu nhiên có thời hạn ngắn. Token chỉ xuất hiện trong MCP result metadata dành cho app được render, không đi vào structured content mà model nhìn thấy và chỉ được các human/live UI API chấp nhận. Việc tự động gắn lại vào cùng `live_id` tái sử dụng credential hiện tại để các view reconnect không làm mất hiệu lực của nhau; nó cũng mang theo logical `session_id` hiện tại để view có thể khôi phục Session bền vững ngay cả khi state Live Workspace trong bộ nhớ đã mất. Một lời gọi `workspace_open` mới, rõ ràng sẽ xoay credential. App nhúng không dùng browser cookie hay ambient credential.

Client không triển khai MCP Apps có thể bỏ qua UI metadata. Tất cả MCP data tools bình thường vẫn khả dụng và giữ nguyên hành vi.

## Prompt đầu tiên

```text
Dùng local-shell-mcp. Trước tiên gọi environment_get, sau đó liệt kê root workspace. Chưa sửa file.
```

Điều này xác minh connectivity mà không thay đổi gì.

## Quy tắc vận hành khuyến nghị

Đưa constraints rõ ràng cho model:

- Làm việc trong `/workspace` trừ khi được chỉ định rõ khác đi.
- Chạy tests trước commit.
- Dùng `secret_scan` trước push.
- Chỉ dùng `link_create` cho file an toàn để chia sẻ.
- Ưu tiên persistent shell sessions cho process dài.
- Tóm tắt mọi command đã thay đổi file.

## Vấn đề tool discovery

Nếu ChatGPT xác thực được nhưng không hiện tools dự kiến:

- Xác nhận endpoint kết thúc bằng `/mcp`.
- Kiểm tra `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Kiểm tra reverse proxy headers và request body limits.
- Xem `docker compose logs --tail=200 local-shell-mcp`.
- Xác nhận service đang ở mode `mcp` hoặc `both`.

## Ghi chú an toàn

Deployment công khai phải giữ OAuth bật. Không công khai MCP tools đầy đủ mà không xác thực trên Internet. Xem mỗi tool được phê duyệt là một phần quyền thực tế của model đã kết nối.
