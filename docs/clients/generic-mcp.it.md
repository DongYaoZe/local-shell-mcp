<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client generici

`local-shell-mcp` può essere usato da ChatGPT e da altri MCP client. Il client decide se collegarsi via HTTP o avviare il server tramite stdio.

## MCP client HTTP

Usa HTTP mode quando il server è già in esecuzione:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint locale:

```text
http://127.0.0.1:8765/mcp
```

Endpoint di rete:

```text
https://your-public-host.example.com/mcp
```

Usa OAuth per qualsiasi endpoint raggiungibile oltre un localhost fidato.

## MCP client stdio

Usa stdio mode quando il client avvia direttamente il processo server:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Forma tipica della configurazione client:

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

Gli schema dei client variano. Alcuni chiamano questa sezione `mcpServers`, altri usano un nome diverso.

## Prima verifica sicura

Per un client appena collegato, inizia con:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Poi esegui un’attività limitata con regole esplicite per modifiche, test e Git.
