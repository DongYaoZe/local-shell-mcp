<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Выбор runtime и модель развёртывания

В `local-shell-mcp` есть два независимых решения:

1. **Runtime**: как запускается процесс сервера и какой workspace он контролирует.
2. **Client connection**: как ChatGPT или другой MCP client достигает этого сервера.

Не рассматривайте ChatGPT как способ развёртывания. ChatGPT — client. Docker, VS Code extension, release binaries, установки Python и stdio mode — варианты runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Типичная публичная схема:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Локальная схема MCP client может быть проще:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Матрица выбора runtime

| Runtime | Лучше всего для | Граница изоляции | Источник toolchain | Публичный доступ ChatGPT | Страница |
|---|---|---|---|---|---|
| Docker Compose | Большинство coding-agent нагрузок и воспроизводимые workspaces | Container | Project image содержит широкий набор инструментов | Добавить HTTPS proxy или tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Публичное развёртывание одним stack с Cloudflare Tunnel | Container | Project image | Встроено в Compose `tunnel` profile | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Запуск/остановка server из editor workspace | Обычно host process | Host tools плюс настроенный executable | Добавить внешний HTTPS tunnel/proxy для ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts/VM, где Docker недоступен | Host or VM | Host tools плюс настроенный executable | Добавить HTTPS proxy или tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native использование, debugging, development | Host virtualenv or VM | Python package плюс host tools | Добавить HTTPS proxy или tunnel | [Python install](../installation/python.md) |
| Stdio mode | Локальные MCP clients, которые напрямую запускают процессы | Client process boundary | Host tools плюс настроенный executable | Нельзя использовать с ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Матрица подключения client

| Путь client | Нужен публичный HTTPS | Использует `/mcp` | Нужен OAuth | Типичный runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Да | Да | Да для публичного использования | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Нет | Нет | Нет | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Обычно нет для localhost; да через сети | Да | Рекомендуется вне localhost | Any HTTP runtime |
| VS Code extension helper flow | Только если нужен ChatGPT | Да при копировании ChatGPT URL | Рекомендуется для ChatGPT | VS Code-launched runtime |

См. [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Что контролирует каждый runtime

Каждый runtime запускает один и тот же server code и при включении предоставляет те же семейства MCP tools:

- Shell и persistent shell sessions.
- Filesystem, search и patch tools.
- Операции Git.
- Browser automation через Playwright.
- Audit log и task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle и machine-routed tools.

Различается не абстрактный API, а **operating environment** за ним.

| Вопрос | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Где выполняются команды? | В container | Обычно в host workspace | В process environment host или VM |
| Default workspace? | Mounted `/workspace` | Текущая папка VS Code или настроенный path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compilers/browsers предустановлены? | Да, широко | Только установленные на host | Только установленные на host |
| Легко сбросить? | Пересоздать container и workspace volume | Зависит от workspace | Зависит от host/VM |
| Подходит для произвольной установки пакетов? | Да, если disposable | Рискованнее на host | Рискованнее вне VM |

## Рекомендуемый выбор

Сначала используйте **Docker Compose**, если нет причины поступить иначе. Он даёт самую ясную safety boundary и самый полный стандартный toolchain.

Используйте **VS Code extension**, когда workflow начинается в editor и нужен local launcher. Это всё ещё runtime. Сам по себе он не делает server доступным ChatGPT; для ChatGPT web/app добавьте tunnel или reverse proxy.

Используйте **standalone binary**, если Docker недоступен, но VM, container host или dedicated user account уже обеспечивают boundary.

Используйте **`pipx` или source install** для development/debugging самого `local-shell-mcp` или когда Python-based environment удобнее поддерживать.

Используйте **stdio mode** только для локальных MCP clients, которые могут spawn server process. Это не публичное deployment и не используется напрямую ChatGPT web/app.

## Правило публичного endpoint

Для HTTP MCP clients вроде ChatGPT MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` — только origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Не добавляйте `/mcp` к `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Страницы runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Страницы client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
