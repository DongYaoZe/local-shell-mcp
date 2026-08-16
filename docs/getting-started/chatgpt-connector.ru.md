<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Коннектор ChatGPT

Эта страница описывает ChatGPT как client-подключение. Она не выбирает runtime. Перед её использованием запустите сервер через Docker, VS Code extension, binary или установку Python.

`local-shell-mcp` предназначен для ChatGPT Developer Mode и полноценных MCP-клиентов. MCP endpoint напрямую предоставляет обычный набор инструментов LSM.

## Требования к runtime

Сначала выберите и запустите один runtime:

| Runtime | Страница |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Затем опубликуйте этот runtime по сетевому пути, доступному ChatGPT. См. [network connectivity](../clients/connectivity.md).

## Публичный URL

ChatGPT должен достигать сервера по HTTPS. MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

Убедитесь, что `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` совпадает с public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Не включайте `/mcp` в `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Настройка OAuth

Рекомендуемые настройки для публичного доступа:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access tokens по умолчанию не истекают, поскольку длинные coding-сессии могут превышать короткие сроки жизни токена. При необходимости отзывайте доступ ротацией JWT secret или повторным развёртыванием со свежим состоянием.

## Добавление коннектора

1. Откройте настройки connector или Developer Mode MCP в ChatGPT.
2. Добавьте custom MCP server.
3. Введите MCP URL: `https://your-public-host.example.com/mcp`.
4. Завершите OAuth.
5. Подтвердите поверхность инструментов.

## Live Workspace MCP App

ChatGPT-клиенты с поддержкой MCP Apps могут отображать `local-shell-mcp` как интерактивный execution workspace. Попросите ChatGPT один раз открыть Live Workspace, когда нужна видимость в реальном времени или совместная работа с человеком; затем приложение переподключается само без повторных вызовов `workspace_open`.

Live Workspace намеренно отделён от reasoning модели. Он показывает наблюдаемое execution state и общие resources:

- **Activity** показывает запуски, завершения и ошибки MCP tools, а также действия человека.
- **Terminal** подключается к существующему backend постоянного shell и показывает live PTY output.
- **Files** позволяет просматривать, preview, edit, create и delete локальные или удалённые workspace-файлы.
- **Diff** показывает staged/unstaged Git changes и может отправить текущий diff обратно в ChatGPT для проверки.
- **Jobs** показывает managed jobs и persistent sessions.
- **Remotes** показывает workers и даёт действия invite, rename и revoke при включённой remote support.
- **Audit** показывает недавние structured MCP audit records.

Live Workspace всегда collaborative: ChatGPT и человек могут одновременно менять один workspace. Если host поддерживает, он открывается плавающим PiP-окном и переключается между fullscreen и оконным режимом. Отдельного observe/takeover state нет.

Представления files, diff, audit и activity могут передавать выбранный operational context в следующий model turn через MCP Apps bridge. Это явно общий context; UI не раскрывает и не восстанавливает private model reasoning.

### Сеть и безопасность

Отображаемое MCP App напрямую подключается из своей sandbox к настроенному service origin для низколатентного terminal/event traffic. Поэтому `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` должен быть HTTPS origin, доступным браузеру ChatGPT. Сам MCP endpoint остаётся `https://your-public-host.example.com/mcp`.

При открытии workspace выпускается случайный короткоживущий bearer token Live Workspace. Он возвращается только в metadata MCP-result, предназначенной для отображаемого приложения, не попадает в structured content, видимый модели, и принимается только human/live UI API. Автоматическое повторное подключение к тому же `live_id` использует текущую credential, поэтому reconnecting views не инвалидируют друг друга; вместе с ней передаётся текущий логический `session_id`, что позволяет восстановить durable Session даже после потери in-memory состояния Live Workspace. Явный новый вызов `workspace_open` ротирует credential. Встроенное приложение не использует browser cookies или ambient credentials.

Клиенты без MCP Apps могут игнорировать UI metadata. Все обычные MCP data tools остаются доступны и ведут себя прежним образом.

## Первый prompt

```text
Используй local-shell-mcp. Сначала вызови environment_get, затем перечисли корень workspace. Пока не меняй файлы.
```

Так можно проверить соединение без изменений.

## Рекомендуемые правила работы

Задавайте модели чёткие ограничения:

- Работать внутри `/workspace`, если явно не указано иное.
- Запускать tests перед commit.
- Использовать `secret_scan` перед push.
- Использовать `link_create` только для файлов, которыми безопасно делиться.
- Для долгих процессов предпочитать persistent shell sessions.
- Резюмировать все команды, которые изменили файлы.

## Проблемы обнаружения инструментов

Если ChatGPT аутентифицируется, но не показывает ожидаемые инструменты:

- Убедитесь, что endpoint заканчивается на `/mcp`.
- Проверьте `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Проверьте заголовки reverse proxy и лимиты request body.
- Просмотрите `docker compose logs --tail=200 local-shell-mcp`.
- Убедитесь, что service работает в режиме `mcp` или `both`.

## Примечания по безопасности

В публичных deployment OAuth должен оставаться включённым. Не публикуйте полный набор MCP tools без аутентификации в открытом Интернете. Считайте каждый одобренный tool частью фактических полномочий подключённой модели.
