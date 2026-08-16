<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Автономный binary runtime

Release binaries запускают `local-shell-mcp` без Docker и Python environment. Используйте этот runtime, когда Docker недоступен либо dedicated VM, container host, lab server или restricted user account уже обеспечивает границу безопасности.

Это выбор runtime. Доступ ChatGPT настраивается отдельно через HTTPS endpoint `/mcp`.

## Release artifacts

GitHub Releases собирает self-contained executable для распространённых платформ:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

Каждый archive содержит executable, README, license и краткий quickstart file.

## Установка

1. Скачайте с GitHub Releases archive для вашей платформы.
2. Распакуйте его.
3. Поместите executable в `PATH` или сохраните его absolute path.
4. Запустите `local-shell-mcp --help`, чтобы проверить запуск binary.

Linux и macOS обычно требуют executable bit:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

Пользователям Windows следует запускать `local-shell-mcp.exe` из PowerShell или добавить содержащий его directory в `PATH`.

## Минимальный локальный запуск

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

В другом terminal:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Публичный HTTP MCP запуск

Для ChatGPT или public HTTP MCP client задайте следующие категории configuration:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Directory, контролируемый tools |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Local bind address и port |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | Public HTTPS origin без `/mcp` |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Для public deployment используйте `oauth` |
| OAuth PIN and JWT secret settings | Требуются для public OAuth authorization |

Опубликуйте local HTTP port через reverse proxy или tunnel. Public endpoint:

```text
https://your-public-host.example.com/mcp
```

## YAML config

YAML config может хранить не секретные runtime defaults:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Запуск:

```bash
local-shell-mcp --config /path/to/config.yaml
```

Environment variables с prefix `LOCAL_SHELL_MCP_` перекрывают YAML values.

## Ответственность за host toolchain

Binary включает Python application, но не все developer tools. MCP tools вызывают программы, доступные на host.

Установите необходимое для ваших задач:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; Linux releases уже включают static tmux helper |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

Если не хотите поддерживать этот host toolchain, используйте Docker Compose.

## Долгоживущий сервис

Для persistent public deployment запускайте binary под process supervisor вашей ОС. Соблюдайте следующие правила:

- Dedicated low-privilege OS account.
- Dedicated workspace directory.
- Sensitive values хранить вне world-readable files.
- Автоматически restart при failure.
- Проверять `/healthz` после каждого restart.
- Сохранять logs для troubleshooting.

## Updates

1. Скачайте новый release archive для платформы.
2. При желании verify checksums.
3. Замените executable.
4. Restart process manager.
5. Проверьте `/healthz`.
6. Перед продолжением работы попросите client выполнить `environment_get`.

## Безопасность

Binary работает с привилегиями OS user. Для public deployment используйте dedicated low-privilege user, dedicated workspace и по возможности VM/container boundary.

Не задавайте `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` для binary, работающего прямо на personal host. Этот параметр предназначен для disposable containers/VMs.
