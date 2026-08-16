<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime tiện ích VS Code

Tiện ích VS Code là launcher và convenience UI cho cùng server `local-shell-mcp`. Đây là lựa chọn runtime vì nó khởi động server process cho editor workspace hiện tại.

Nó không phải ChatGPT connector. Khi dùng web/app, ChatGPT vẫn kết nối tới public HTTPS `/mcp` endpoint.

## Tiện ích làm gì

Tiện ích:

- Khởi động `local-shell-mcp` cho VS Code workspace hiện tại.
- Stop và restart server.
- Hiển thị server output trong VS Code output channel.
- Kiểm tra `/healthz`.
- Copy MCP URL.
- Copy ChatGPT setup prompt chứa workspace và endpoint.

Tiện ích không bundle server binary. Cài `local-shell-mcp` riêng rồi trỏ extension tới executable nếu nó không ở `PATH`.

## Khi nào dùng

Dùng runtime này khi:

- Bạn thường bắt đầu từ VS Code folder.
- Muốn button/command-palette flow thay vì tự chạy terminal command.
- Project dependencies đã được cài trên host.
- Đang làm với trusted repositories hoặc workspace hẹp.
- Chấp nhận expose chỉ workspace đó cho model.

Dùng Docker khi:

- Repository untrusted.
- Task sẽ install arbitrary packages.
- Cần broad preinstalled toolchain.
- Muốn reset dễ bằng cách tạo lại container.
- Muốn boundary rõ hơn host account.

## Cài executable

Chọn một server install method:

```bash
pipx install local-shell-mcp
```

hoặc download release binary cho OS và đặt vào `PATH`.

Sau đó install VSIX release asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Hoặc dùng **Extensions: Install from VSIX...** trong command palette.

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace expose cho MCP | Empty cho VS Code folder đầu tiên hoặc explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin được copy vào prompts và URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN cho OAuth authorization | Strong random value khi dùng công khai |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Giữ `false` khi direct host usage |
| `local-shell-mcp.extraEnv` | Extra environment cho server process | Chỉ project-specific safe values |

## Basic flow

1. Mở project folder trong VS Code.
2. Chạy **local-shell-mcp: Start Server**.
3. Chạy **Show Server Status** hoặc **Check Health** nếu có.
4. Dùng **Copy MCP URL** cho local MCP client hoặc **Copy ChatGPT Setup Prompt** cho ChatGPT.
5. Thêm endpoint vào client.

Local endpoint thường là:

```text
http://127.0.0.1:8765/mcp
```

Hữu ích cho local clients nhưng ChatGPT web/app không truy cập được.

## Dùng với ChatGPT

Để dùng VS Code-launched server từ ChatGPT, thêm HTTPS tunnel hoặc reverse proxy trước local port.

Ví dụ:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Set:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

URL copy cho ChatGPT phải kết thúc `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Tiện ích thường chạy commands dưới host user. Điều này khác đáng kể với disposable Docker container.

Quy tắc khuyến nghị:

- Chỉ mở repository bạn muốn model kiểm soát.
- Giữ `allowFullContainer` tắt.
- Không set workspace root thành home directory.
- Không giữ unrelated secrets trong workspace.
- Dùng `secret_scan` trước commit/push.
- Ưu tiên Docker cho unfamiliar repositories hoặc package-install-heavy tasks.

## Common prompt

Sau khi copy setup prompt, bắt đầu bằng read-only task:

```text
Dùng local-shell-mcp. Trước tiên gọi environment_get và file_tree trên workspace. Chưa sửa file.
```

Sau đó chuyển sang bounded edit:

```text
Sửa failing test trong workspace này. Đọc relevant files trước, tạo patch nhỏ nhất, chạy targeted test và hiển thị git diff. Không commit cho tới khi tôi chấp thuận.
```

## Troubleshooting

| Triệu chứng | Kiểm tra |
|---|---|
| Extension không khởi động được server | Xác nhận `local-shell-mcp.executablePath` tồn tại và chạy được `--help` trong terminal |
| ChatGPT không truy cập được | Local `127.0.0.1` URL không public; cấu hình tunnel/proxy và `publicBaseUrl` |
| Tools expose nhầm folder | Set `local-shell-mcp.workspaceRoot` rõ ràng |
| Auth lỗi sau restart | Set OAuth admin PIN và JWT secret ổn định qua `extraEnv` hoặc runtime configuration |
| Commands thiếu dependencies | Cài dependencies trên host hoặc chuyển sang Docker runtime |
