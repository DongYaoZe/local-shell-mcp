<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# Generische MCP client

`local-shell-mcp` kann von ChatGPT und anderen MCP client verwendet werden. Der client entscheidet, ob er sich über HTTP verbindet oder den Server über stdio startet.

## HTTP-MCP-client

Verwenden Sie HTTP mode, wenn der Server bereits läuft:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Lokaler Endpoint:

```text
http://127.0.0.1:8765/mcp
```

Netzwerk-Endpoint:

```text
https://your-public-host.example.com/mcp
```

Verwenden Sie OAuth für jeden Endpoint, der über vertrauenswürdiges localhost hinaus erreichbar ist.

## Stdio-MCP-client

Verwenden Sie stdio mode, wenn der client den Serverprozess selbst startet:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Typische client-Konfiguration:

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

Client-Schemas unterscheiden sich. Manche nennen diesen Abschnitt `mcpServers`, andere verwenden einen anderen Namen.

## Erste sichere Prüfung

Beginnen Sie bei einem neu verbundenen client mit:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Führen Sie anschließend eine klar begrenzte Aufgabe mit expliziten Regeln für Bearbeitung, Tests und Git aus.
