<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Файловые ссылки

`local-shell-mcp` может предоставлять файлы из контролируемого workspace через высокоэнтропийные bearer URL. Это удобно, когда ИИ создаёт отчёты, архивы, PDF, screenshots или другие artifacts, которые нужно скачать из чата или отобразить в нём.

## Когда использовать файловые ссылки

Используйте их для:

- Созданных PDF или отчётов.
- Screenshots и browser artifacts.
- Результатов build.
- Logs, слишком больших для вставки в чат.
- Архивов для ручной проверки.

Не используйте файловые ссылки для secrets, private keys, хранилищ credentials или посторонних персональных данных.

## Типичный порядок

1. Создайте или найдите файл в `/workspace`.
2. Вызовите `link_create` с TTL и необязательным ограничением числа скачиваний. Установите `inline=true`, если файл должен отображаться прямо в браузере или как Markdown image; по умолчанию используется `false`, что принудительно включает attachment download.
3. Поделитесь возвращённым URL.
4. Отзовите ссылку, когда она больше не нужна.

## Связанные инструменты

| Tool | Назначение |
|---|---|
| `link_create` | Создать токенизированный URL для файла workspace. |
| `link_list` | Показать активные ссылки. |
| `link_revoke` | Отключить ссылку до истечения срока. |

## Управление

Параметры конфигурации включают:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Для чувствительных artifacts используйте короткие TTL и задавайте maximum download count, если ссылка предназначена одному получателю.

## Безопасность

Файловые ссылки — это bearer URL. Любой, у кого есть URL, может скачать файл до истечения срока, достижения download limit или отзыва ссылки. Относитесь к ним как к временным secrets. Inline responses включают CSP sandbox и `X-Content-Type-Options: nosniff`, поэтому активные форматы не могут обращаться к LSM origin или выполняться как unsandboxed same-origin content.
