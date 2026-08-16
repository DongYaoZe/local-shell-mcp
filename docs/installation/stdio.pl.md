<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Tryb stdio jest przeznaczony dla lokalnych MCP client, które uruchamiają `local-shell-mcp` jako child process i komunikują się przez standardowe wejście/wyjście.

Nie jest to publiczny deployment HTTP. ChatGPT web/app nie może korzystać z niego bezpośrednio, ponieważ ChatGPT nie może uruchomić process na Twojej maszynie.

## Kiedy używać stdio

Używaj stdio mode, gdy:

- MCP client obsługuje command-based server definitions.
- Client i kontrolowany workspace znajdują się na tej samej maszynie.
- Nie potrzebujesz OAuth, publicznego HTTPS, reverse proxy ani tunnel.
- Chcesz, aby client zarządzał server lifecycle.

Nie używaj stdio mode, gdy:

- Client to ChatGPT web/app.
- Wiele remote clients potrzebuje tego samego server.
- Potrzebujesz tokenized file download przez HTTP.
- Potrzebujesz remote-worker join routes obsługiwanych przez HTTP.

## Polecenie

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Ogólna konfiguracja MCP client zwykle zawiera:

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

Dostosuj schema do swojego client. Niektóre clients nazywają tę sekcję `servers`, `tools`, `mcpServers` lub `contextServers`.

## Różnice względem HTTP mode

| Obszar | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Brak | `/mcp` |
| OAuth | Niepotrzebny | Zalecany dla użycia publicznego |
| Health endpoint | Brak | `/healthz`, `/readyz` |
| Publiczne użycie ChatGPT | Nie | Tak, za HTTPS |
| Server lifecycle | client uruchamia process | Ty zarządzasz process/runtime |

Poza tym tool surface używa tej samej server-side implementation, z uwzględnieniem configuration i wsparcia client.

## Uwagi o bezpieczeństwie

Stdio mode często działa bezpośrednio na host jako ten sam user co MCP client. Używaj wąskiego workspace root i unikaj szerokiego filesystem access. Pozostaw full-container mode wyłączony, chyba że stdio samo działa w jednorazowym container lub VM.
