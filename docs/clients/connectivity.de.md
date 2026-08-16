<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Netzwerkverbindung

HTTP-MCP-client außerhalb der Maschine benötigen einen erreichbaren HTTPS-Origin. Diese Seite behandelt das Netzwerk-Routing, nicht die Wahl des Runtime.

Der client endpoint endet normalerweise auf `/mcp`:

```text
https://your-public-host.example.com/mcp
```

Die public base URL des Servers enthält nur den Origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Nehmen Sie `/mcp` nicht in diese base URL auf.

## Verbindungsoptionen

| Option | Einsatz |
|---|---|
| Compose tunnel sidecar | Docker Compose mit dem eingebauten `tunnel`-Profile |
| Externer Tunnel | Jeder Runtime, der außerhalb des lokalen Netzes erreichbar sein muss |
| Caddy | Einfaches automatisches TLS |
| Nginx oder Nginx Proxy Manager | Vorhandene Nginx-Infrastruktur |
| Traefik | Vorhandenes container-natives Routing |

## Pfade

Leiten Sie den gesamten Origin an den laufenden Server weiter. Wichtige Pfade sind:

| Pfad | Zweck |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Health Checks |
| `/.well-known/...` | Metadaten zur client discovery |
| `/oauth/...` | Autorisierungsablauf des client |
| `/downloads/...` | Optionale Links zu generierten Dateien |
| `/join/...`, `/remote/...` | Optionaler remote-worker-Ablauf |

## Proxy-Verhalten

Der Proxy sollte Pfade unverändert lassen, request bodies weiterleiten, lange responses unterstützen und sehr kurze Timeouts vermeiden.

## Prüfungen

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Häufige Fehler

| Fehler | Korrektur |
|---|---|
| In ChatGPT `https://host` statt `https://host/mcp` verwenden | `/mcp` nur am client endpoint ergänzen |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` setzen | Nur den Origin setzen |
| Nur `/mcp` routen | Den gesamten Origin routen, damit Discovery und Autorisierung ebenfalls funktionieren |
| Einen host runtime mit zu breitem Workspace ausführen | Einen engen Workspace oder Docker verwenden |

## Empfohlene Kombinationen

| Runtime | Netzwerkmuster |
|---|---|
| Docker Compose auf einem Server | Vorhandener Reverse Proxy oder Compose tunnel profile |
| Docker Compose auf einem Heimrechner | Outbound tunnel |
| VS Code extension auf einem Laptop | Temporärer Tunnel für die Sitzung |
| Binary auf einer VM | Reverse Proxy auf der VM oder am Netzwerkrand |
| Python/source-Entwicklungsserver | Normalerweise nur localhost |
| Stdio mode | Kein HTTP-Netzpfad; lokalen MCP client verwenden |
