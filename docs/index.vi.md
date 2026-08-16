<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">MCP control plane tương thích ChatGPT</span>

# local-shell-mcp

Cung cấp cho AI assistant shell được kiểm soát, workspace thực, Git, browser automation, file sharing và remote-worker access mà không rời chat.

<div class="hero-actions" markdown>
[Bắt đầu](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Chọn runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Tham chiếu tools](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Môi trường coding thực
Chạy tests, kiểm tra repositories, patch files, vận hành Git và giữ audit trail từ một MCP endpoint.
</div>

<div class="feature-card" markdown>
### Các lớp runtime và client
Chọn runtime như Docker, VS Code extension, binary, Python hoặc stdio, rồi kết nối ChatGPT hay MCP client khác riêng biệt.
</div>

<div class="feature-card" markdown>
### Điều khiển remote machine
Gắn máy sau NAT, firewall hoặc HPC qua outbound worker connections mà không mở SSH ports.
</div>
</div>

## Cung cấp những gì

`local-shell-mcp` cung cấp workspace local hoặc container có kiểm soát cho ChatGPT và các MCP client khác. Nó cung cấp shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, logical Session bền vững với Goal Plan tùy chọn, tokenized file link và remote-worker tool qua MCP server tương thích ChatGPT có OAuth.

Dùng khi AI cần inspect repository, chạy tests, edit files, operate Git, thu browser evidence, tạo downloadable artifacts hoặc điều khiển remote machine chỉ có thể outbound connect tới control server.

## Kiến trúc

```text
Lớp runtime: Docker / VS Code extension / binary / Python / stdio
Lớp exposure: localhost / HTTPS proxy / tunnel / stdio pipe
Lớp client: ChatGPT / generic MCP client / editor helper
Workspace được kiểm soát: /workspace or configured workspace root
Remote workers tùy chọn: outbound machine connections
```

Isolation boundary dự kiến là container hoặc VM chạy service.

## Bắt đầu theo kịch bản

| Kịch bản | Bắt đầu ở đây | Lý do |
|---|---|---|
| Public ChatGPT deployment đầu tiên | [Quickstart](getting-started/quickstart.md) | Đường Docker Compose với OAuth và setup `/mcp` |
| Chọn runtime layer | [Runtime choices](guides/deployment.md) | Giải thích Docker, VS Code, binary, Python và stdio là các runtime option riêng |
| Thêm ChatGPT làm client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, prompt an toàn đầu tiên, tool discovery |
| Thêm LSM vào DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Cài repository này như DSH bundle đồng thời giữ toàn bộ LSM tool và remote-worker surface |
| Chạy từ VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime và lưu ý host safety |
| Học cách vận hành toolset | [Usage patterns](guides/usage-patterns.md) | Prompt templates và hướng dẫn chọn tools |
| Hiểu từng tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations và notes của từng tool |
| Kết nối HPC, NPU/GPU hoặc server node | [Remote workers](guides/remote-workers.md) | Outbound worker join flow và remote tool usage |
| Chia sẻ generated files | [File links](guides/file-links.md) | Tokenized download URL có TTL và revocation |
| Harden deployment | [Security](security.md) | Isolation, OAuth, workspace scope và audit logs |

## Các family tool chính

| Family | Ví dụ | Dùng cho |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection và precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Reviewable source-control workflows |
| Sessions và goals | `session_manage`, `plan_manage` | Durable task handoff, progress report và optional Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI checks, screenshots, rendered docs, page text |
| File links | `link_create`, `link_revoke` | Download generated artifacts từ chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Machines sau NAT, firewalls hoặc cluster login flows |

## Workflow điển hình

### Coding với ChatGPT

1. Khởi động runtime như Docker Compose, VS Code extension, binary hoặc Python trong dedicated workspace.
2. Expose HTTP runtime nếu ChatGPT cần network access.
3. Thêm public `/mcp` endpoint vào ChatGPT.
4. Trước tiên yêu cầu inspect repository và chạy read-only checks.
5. Sau khi chấp thuận, cho phép patch files, tests, diff review, commit và push.
6. Review audit log khi task liên quan file links hoặc remote systems.

### Remote HPC hoặc accelerator host

1. Tạo one-time remote worker invite.
2. Dán generated command trên remote host.
3. Dùng normal tools với `machine`; Git qua `run_shell` và transfer qua `remote_transfer`.
4. Revoke worker sau task.

### Artifact generation

1. Để AI generate file dưới `/workspace`.
2. Tạo tokenized file link với TTL/download limits.
3. Chia sẻ link trong chat.
4. Revoke khi xong.

## Ngôn ngữ

Site này được build bằng native MkDocs i18n plugin. Dùng language selector trong header để chuyển giữa English và translated pages. Page không có translation fallback sang English.
