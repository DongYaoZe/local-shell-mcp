<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Runtime Python, pipx và source

Runtime Python hữu ích cho phát triển, gỡ lỗi và các môi trường nơi quản lý package Python dễ hơn Docker. Chúng chạy cùng server với runtime Docker và binary.

Dùng trang này cho ba trường hợp liên quan:

- `pipx install local-shell-mcp`: cài executable cấp người dùng.
- `pip install local-shell-mcp`: cài vào virtual environment hiện có.
- Editable source checkout: phát triển hoặc gỡ lỗi chính project.

## Cài bằng pipx

`pipx` là cách cài dựa trên Python sạch nhất cho người dùng thông thường vì mỗi command có virtual environment riêng trong khi executable vẫn được đưa lên `PATH`.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Khởi động server MCP HTTP cục bộ:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Kiểm tra sức khỏe:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Cài trong virtual environment

Dùng khi bạn đã tự quản lý các môi trường Python:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Process dùng các tool đã cài trên host. Package Python không tự cài compiler, Git, browser system dependency hoặc project dependency cho bạn.

## Editable source checkout

Dùng để phát triển project:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Chạy kiểm tra:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Thiết lập trình duyệt

Package Python phụ thuộc Playwright, nhưng browser binary vẫn có thể cần cài trên host:

```bash
python -m playwright install chromium
```

Một số host Linux cần browser dependency bổ sung. Docker tránh được phần lớn việc này vì image bắt đầu từ Playwright base image.

## Dùng HTTP MCP công khai

Với ChatGPT hoặc public HTTP MCP client khác, cấu hình cùng public-origin và OAuth như các runtime HTTP khác, sau đó expose local port qua reverse proxy hoặc tunnel.

Endpoint MCP công khai:

```text
https://your-public-host.example.com/mcp
```

## Chế độ phát triển

| Mode | Command | Sử dụng |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | MCP client đầy đủ qua HTTP, gồm ChatGPT sau HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Endpoint chẩn đoán hoặc tương thích, không phải đường chính của ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | MCP client cục bộ tự khởi chạy process |

`mode=both` được dành riêng và hiện không nên dùng như mode của một process đơn lẻ.

## An toàn host runtime

Cài đặt Python chạy với quyền host user trừ khi đặt trong VM/container. Giữ workspace hẹp, full-container mode tắt và không trỏ workspace tới home directory.

Dùng Docker Compose cho repository không tin cậy, task dùng nhiều package manager hoặc workflow mà resetability quan trọng hơn tích hợp host.
