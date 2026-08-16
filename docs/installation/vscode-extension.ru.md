<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime расширения VS Code

Расширение VS Code — launcher и удобный UI для того же сервера `local-shell-mcp`. Это выбор runtime, потому что оно запускает процесс сервера для текущего editor workspace.

Это не сам ChatGPT connector. При использовании web/app ChatGPT всё равно подключается к публичному HTTPS endpoint `/mcp`.

## Что делает расширение

Расширение:

- Запускает `local-shell-mcp` для текущего VS Code workspace.
- Останавливает и перезапускает server.
- Показывает server output в VS Code output channel.
- Проверяет `/healthz`.
- Копирует MCP URL.
- Копирует ChatGPT setup prompt с workspace и endpoint.

Расширение не включает server binary. Установите `local-shell-mcp` отдельно и укажите executable, если он не находится в `PATH`.

## Когда использовать

Используйте этот runtime, если:

- Обычно начинаете работу из VS Code folder.
- Нужен button/command-palette flow вместо ручного запуска terminal command.
- Project dependencies уже установлены на host.
- Работаете с trusted repositories или узким workspace.
- Готовы открыть модели только этот workspace.

Используйте Docker, если:

- Repository untrusted.
- Task будет устанавливать arbitrary packages.
- Нужен широкий preinstalled toolchain.
- Нужен лёгкий reset через пересоздание container.
- Нужна более чистая boundary, чем host account.

## Установка executable

Выберите один способ установки server:

```bash
pipx install local-shell-mcp
```

или скачайте release binary для OS и поместите его в `PATH`.

Затем установите VSIX release asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Либо используйте **Extensions: Install from VSIX...** в command palette.

## Настройки расширения

| Setting | Назначение | Типичное значение |
|---|---|---|
| `local-shell-mcp.executablePath` | Path к server executable | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Bind address локального server | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace, открытый MCP | Empty для первой папки VS Code или explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin, копируемый в prompts/URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN для OAuth authorization | Strong random value для public use |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Для direct host usage оставлять `false` |
| `local-shell-mcp.extraEnv` | Extra environment для server process | Только project-specific safe values |

## Базовый flow

1. Откройте project folder в VS Code.
2. Запустите **local-shell-mcp: Start Server**.
3. Запустите **Show Server Status** или **Check Health**, если доступно.
4. Используйте **Copy MCP URL** для local MCP client или **Copy ChatGPT Setup Prompt** для ChatGPT.
5. Добавьте endpoint в client.

Local endpoint обычно выглядит так:

```text
http://127.0.0.1:8765/mcp
```

Он полезен local clients, но недоступен ChatGPT web/app.

## Использование с ChatGPT

Чтобы использовать VS Code-launched server с ChatGPT, добавьте HTTPS tunnel или reverse proxy перед local port.

Пример:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Установите:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

URL для ChatGPT должен заканчиваться `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Безопасность host runtime

Расширение обычно выполняет commands с правами host user. Это существенно отличается от disposable Docker container.

Рекомендуемые правила:

- Открывайте только repository, который должен контролировать model.
- Оставляйте `allowFullContainer` выключенным.
- Не задавайте workspace root равным home directory.
- Не храните unrelated secrets в workspace.
- Используйте `secret_scan` перед commit/push.
- Предпочитайте Docker для unfamiliar repositories или package-install-heavy tasks.

## Обычный prompt

После копирования setup prompt начните с read-only task:

```text
Используй local-shell-mcp. Сначала вызови environment_get и file_tree для workspace. Пока не изменяй файлы.
```

Затем перейдите к bounded edit:

```text
Исправь failing test в этом workspace. Сначала прочитай relevant files, сделай минимальный patch, запусти targeted test и покажи git diff. Не делай commit до моего подтверждения.
```

## Диагностика

| Симптом | Проверка |
|---|---|
| Extension не может запустить server | Проверить, что `local-shell-mcp.executablePath` существует и `--help` работает в terminal |
| ChatGPT не может подключиться | Local `127.0.0.1` URL не public; настроить tunnel/proxy и `publicBaseUrl` |
| Tools открывают неправильную folder | Явно задать `local-shell-mcp.workspaceRoot` |
| Auth ломается после restart | Задать стабильные OAuth admin PIN и JWT secret через `extraEnv` или runtime configuration |
| Commands не находят dependencies | Установить dependencies на host или перейти на Docker runtime |
