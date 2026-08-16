<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

Основной интерфейс — MCP на `/mcp`. REST surface также доступна для health checks, file links и отдельных service operations.

## Состояние

```http
GET /healthz
```

Возвращает состояние сервера и базовую информацию о его работе.

## MCP

```http
POST /mcp
```

Streamable HTTP MCP endpoint, используемый ChatGPT и другими MCP client.

## Вызовы инструментов через REST

REST-вызовы инструментов используют единые envelopes для успеха и ошибок. Ошибки валидации возвращают структурированные payloads `ok: false`, а не необработанные исключения фреймворка.

## Agent Skills

Фиксированный реестр Skills также доступен через REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Изменения каталогов Skill видны при следующем вызове и не меняют список MCP-инструментов.

## Файловые ссылки

Токенизированные загрузки файлов обслуживает встроенное HTTP-приложение. Ссылки являются bearer URL с TTL, необязательным максимальным числом скачиваний и поддержкой отзыва.

## Аутентификация

Для публичных развёртываний следует использовать OAuth. Для разработки можно включить localhost bypass, однако неаутентифицированный публичный доступ небезопасен.
