<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Сетевая доступность

HTTP MCP client за пределами машины нужен доступный HTTPS origin. Эта страница посвящена сетевой маршрутизации, а не выбору runtime.

client endpoint обычно заканчивается на `/mcp`:

```text
https://your-public-host.example.com/mcp
```

Параметр public base URL сервера содержит только origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Не добавляйте `/mcp` в этот base URL.

## Варианты подключения

| Вариант | Когда использовать |
|---|---|
| Compose tunnel sidecar | Docker Compose со встроенным profile `tunnel` |
| Внешний tunnel | Любой runtime, который должен быть доступен вне локальной сети |
| Caddy | Простая автоматическая настройка TLS |
| Nginx или Nginx Proxy Manager | Существующая инфраструктура Nginx |
| Traefik | Существующая container-native маршрутизация |

## Пути

Проксируйте весь origin на работающий сервер. Важные пути:

| Путь | Назначение |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Проверки состояния |
| `/.well-known/...` | Метаданные client discovery |
| `/oauth/...` | Поток авторизации client |
| `/downloads/...` | Необязательные ссылки на созданные файлы |
| `/join/...`, `/remote/...` | Необязательный поток remote-worker |

## Поведение прокси

Прокси должен сохранять пути, передавать request bodies, поддерживать долгие responses и не использовать слишком короткие timeout.

## Проверки

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Типичные ошибки

| Ошибка | Исправление |
|---|---|
| Использовать в ChatGPT `https://host` вместо `https://host/mcp` | Добавить `/mcp` только в client endpoint |
| Задать `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Указать только origin |
| Проксировать только `/mcp` | Проксировать весь origin, чтобы работали discovery и авторизация |
| Запускать host runtime со слишком широким workspace | Использовать узкий workspace или Docker |

## Рекомендуемые сочетания

| Runtime | Сетевая схема |
|---|---|
| Docker Compose на сервере | Существующий reverse proxy или Compose tunnel profile |
| Docker Compose на домашней машине | Outbound tunnel |
| VS Code extension на ноутбуке | Временный tunnel на время сеанса |
| Binary на VM | Reverse proxy на VM или границе сети |
| Python/source dev server | Обычно только localhost |
| Stdio mode | Нет HTTP-маршрута; используйте локальный MCP client |
