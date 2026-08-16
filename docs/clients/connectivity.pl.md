<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Łączność sieciowa

HTTP MCP client znajdujące się poza maszyną potrzebują osiągalnego HTTPS origin. Ta strona dotyczy routingu sieciowego, a nie wyboru runtime.

client endpoint zwykle kończy się na `/mcp`:

```text
https://your-public-host.example.com/mcp
```

Ustawienie public base URL serwera zawiera wyłącznie origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Nie dodawaj `/mcp` do tego base URL.

## Opcje łączności

| Opcja | Kiedy używać |
|---|---|
| Compose tunnel sidecar | Docker Compose z wbudowanym profile `tunnel` |
| Zewnętrzny tunnel | Dowolny runtime, który musi być osiągalny spoza sieci lokalnej |
| Caddy | Prosty automatyczny TLS |
| Nginx lub Nginx Proxy Manager | Istniejąca infrastruktura Nginx |
| Traefik | Istniejący routing container-native |

## Ścieżki

Przekieruj cały origin do uruchomionego serwera. Ważne ścieżki obejmują:

| Ścieżka | Zastosowanie |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Kontrole stanu |
| `/.well-known/...` | Metadane client discovery |
| `/oauth/...` | Przepływ autoryzacji client |
| `/downloads/...` | Opcjonalne linki do wygenerowanych plików |
| `/join/...`, `/remote/...` | Opcjonalny przepływ remote-worker |

## Zachowanie proxy

Proxy powinno zachowywać ścieżki, przekazywać request body, obsługiwać długie response’y i unikać bardzo krótkich timeoutów.

## Kontrole

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Częste błędy

| Błąd | Naprawa |
|---|---|
| Użycie w ChatGPT `https://host` zamiast `https://host/mcp` | Dodaj `/mcp` tylko do client endpoint |
| Ustawienie `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Ustaw tylko origin |
| Routing tylko `/mcp` | Routuj cały origin, aby działały także discovery i autoryzacja |
| Uruchamianie host runtime ze zbyt szerokim workspace | Użyj wąskiego workspace lub Docker |

## Sugerowane połączenia

| Runtime | Schemat sieci |
|---|---|
| Docker Compose na serwerze | Istniejący reverse proxy lub Compose tunnel profile |
| Docker Compose na komputerze domowym | Outbound tunnel |
| VS Code extension na laptopie | Tymczasowy tunnel na czas sesji |
| Binary na VM | Reverse proxy na VM lub brzegu sieci |
| Python/source dev server | Zwykle tylko localhost |
| Stdio mode | Brak ścieżki HTTP; użyj lokalnego MCP client |
