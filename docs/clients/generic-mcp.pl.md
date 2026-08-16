<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# Ogólne MCP client

`local-shell-mcp` może być używany przez ChatGPT i inne MCP client. Client decyduje, czy łączy się przez HTTP, czy uruchamia serwer przez stdio.

## HTTP MCP client

Użyj HTTP mode, gdy serwer już działa:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Lokalny endpoint:

```text
http://127.0.0.1:8765/mcp
```

Sieciowy endpoint:

```text
https://your-public-host.example.com/mcp
```

Używaj OAuth dla każdego endpointu osiągalnego poza zaufanym localhost.

## Stdio MCP client

Użyj stdio mode, gdy client sam uruchamia proces serwera:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Typowy kształt konfiguracji client:

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

Schema clientów różnią się. Niektóre nazywają tę sekcję `mcpServers`, inne używają innej nazwy.

## Pierwsza bezpieczna kontrola

Dla nowo podłączonego client zacznij od:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Następnie uruchom ograniczone zadanie z jawnymi zasadami edycji, testów i Git.
