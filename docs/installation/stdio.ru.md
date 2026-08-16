<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Режим stdio предназначен для локальных MCP client, которые запускают `local-shell-mcp` как child process и обмениваются данными через стандартный ввод/вывод.

Это не публичный HTTP deployment. ChatGPT web/app не может использовать его напрямую, поскольку ChatGPT не способен запустить process на вашей машине.

## Когда использовать stdio

Используйте stdio mode, если:

- MCP client поддерживает command-based server definition.
- client и контролируемый workspace находятся на одной машине.
- OAuth, публичный HTTPS, reverse proxy и tunnel не нужны.
- Вы хотите, чтобы client управлял server lifecycle.

Не используйте stdio mode, если:

- client — ChatGPT web/app.
- Нескольким remote clients нужен один server.
- Нужны tokenized file downloads через HTTP.
- Нужны remote-worker join routes, обслуживаемые по HTTP.

## Команда

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Типичная конфигурация MCP client обычно содержит:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Адаптируйте schema к вашему client. Некоторые clients называют этот раздел `servers`, `tools`, `mcpServers` или `contextServers`.

## Отличия от HTTP mode

| Область | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Нет | `/mcp` |
| OAuth | Не нужен | Рекомендуется для публичного использования |
| Health endpoint | Нет | `/healthz`, `/readyz` |
| Публичное использование ChatGPT | Нет | Да, за HTTPS |
| Server lifecycle | client запускает process | Вы управляете process/runtime |

В остальном tool surface использует ту же server-side implementation с учётом configuration и поддержки client.

## Безопасность

Stdio mode часто работает непосредственно на host от того же пользователя, что и MCP client. Ограничивайте workspace root и избегайте широкого filesystem access. Оставляйте full-container mode отключённым, если stdio не запущен внутри одноразового container или VM.
