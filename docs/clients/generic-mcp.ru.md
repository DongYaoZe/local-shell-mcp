<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# Универсальные MCP client

`local-shell-mcp` можно использовать из ChatGPT и других MCP client. Client решает, подключаться ли по HTTP или запускать сервер через stdio.

## HTTP MCP client

Используйте HTTP mode, когда сервер уже запущен:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Локальный endpoint:

```text
http://127.0.0.1:8765/mcp
```

Сетевой endpoint:

```text
https://your-public-host.example.com/mcp
```

Используйте OAuth для любого endpoint, доступного за пределами доверенного localhost.

## Stdio MCP client

Используйте stdio mode, когда client сам запускает процесс сервера:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Типичная форма настройки client:

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

Schema клиентов различаются. Некоторые называют этот раздел `mcpServers`, другие используют другое имя.

## Первая безопасная проверка

Для только что подключённого client начните с:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Затем выполняйте ограниченную задачу с явными правилами редактирования, тестирования и Git.
