<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio-Runtime

Der Stdio-Modus ist für lokale MCP-Clients gedacht, die `local-shell-mcp` als Child-Prozess starten und über Standardein-/ausgabe kommunizieren.

Es handelt sich nicht um eine öffentliche HTTP-Bereitstellung. ChatGPT web/app kann ihn nicht direkt verwenden, da ChatGPT keinen Prozess auf Ihrer Maschine starten kann.

## Wann stdio verwenden

Verwenden Sie den Stdio-Modus, wenn:

- Ihr MCP-Client befehlsbasierte Serverdefinitionen unterstützt.
- Client und kontrollierter Workspace auf derselben Maschine liegen.
- Sie kein OAuth, öffentliches HTTPS, Reverse Proxies oder Tunnel benötigen.
- Der Client den Server-Lifecycle verwalten soll.

Verwenden Sie den Stdio-Modus nicht, wenn:

- Der Client ChatGPT web/app ist.
- Mehrere Remote-Clients denselben Server benötigen.
- Tokenisierte Dateidownloads über HTTP benötigt werden.
- Remote-Worker-Join-Routen über HTTP benötigt werden.

## Befehl

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Eine generische MCP-Client-Konfiguration enthält typischerweise:

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

Passen Sie das Schema an Ihren Client an. Manche Clients nennen diesen Abschnitt `servers`, `tools`, `mcpServers` oder `contextServers`.

## Verhaltensunterschiede zum HTTP-Modus

| Bereich | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Keiner | `/mcp` |
| OAuth | Nicht erforderlich | Für öffentlichen Einsatz empfohlen |
| Health endpoint | Keiner | `/healthz`, `/readyz` |
| Öffentliche ChatGPT-Nutzung | Nein | Ja, hinter HTTPS |
| Server lifecycle | Client startet Prozess | Sie verwalten Prozess/Runtime |

Die Tool-Oberfläche nutzt ansonsten dieselbe serverseitige Implementierung, abhängig von Konfiguration und Client-Unterstützung.

## Sicherheitshinweise

Der Stdio-Modus läuft häufig direkt auf dem Host unter demselben Benutzer wie der MCP-Client. Verwenden Sie einen eng begrenzten Workspace-Root und vermeiden Sie breiten Dateisystemzugriff. Lassen Sie den Full-Container-Modus deaktiviert, sofern stdio nicht selbst in einem wegwerfbaren Container oder einer VM läuft.
