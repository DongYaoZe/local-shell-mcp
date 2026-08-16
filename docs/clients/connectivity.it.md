<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Connettività di rete

Gli MCP client HTTP esterni alla macchina richiedono un HTTPS origin raggiungibile. Questa pagina riguarda il routing di rete, non la scelta del runtime.

Il client endpoint termina normalmente con `/mcp`:

```text
https://your-public-host.example.com/mcp
```

L’impostazione public base URL del server contiene solo l’origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Non includere `/mcp` in questa base URL.

## Opzioni di connettività

| Opzione | Quando usarla |
|---|---|
| Compose tunnel sidecar | Docker Compose con il profile `tunnel` integrato |
| Tunnel esterno | Qualsiasi runtime che debba essere raggiungibile fuori dalla rete locale |
| Caddy | TLS automatico semplice |
| Nginx o Nginx Proxy Manager | Infrastruttura Nginx esistente |
| Traefik | Routing container-native esistente |

## Percorsi

Inoltra l’intero origin al server in esecuzione. I percorsi importanti includono:

| Percorso | Scopo |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Controlli di stato |
| `/.well-known/...` | Metadati di discovery del client |
| `/oauth/...` | Flusso di autorizzazione del client |
| `/downloads/...` | Link opzionali ai file generati |
| `/join/...`, `/remote/...` | Flusso remote-worker opzionale |

## Comportamento del proxy

Il proxy deve preservare i percorsi, inoltrare i request bodies, supportare responses lunghe ed evitare timeout troppo brevi.

## Controlli

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Errori comuni

| Errore | Correzione |
|---|---|
| Usare `https://host` in ChatGPT invece di `https://host/mcp` | Aggiungere `/mcp` solo al client endpoint |
| Impostare `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Impostare solo l’origin |
| Inoltrare solo `/mcp` | Inoltrare tutto l’origin in modo che funzionino anche discovery e autorizzazione |
| Eseguire un host runtime con workspace troppo ampio | Usare un workspace ristretto o Docker |

## Abbinamento consigliato

| Runtime | Schema di rete |
|---|---|
| Docker Compose su server | Reverse proxy esistente o Compose tunnel profile |
| Docker Compose su macchina domestica | Outbound tunnel |
| VS Code extension su laptop | Tunnel temporaneo per la sessione |
| Binary su VM | Reverse proxy sulla VM o al bordo della rete |
| Server di sviluppo Python/source | Di solito solo localhost |
| Stdio mode | Nessun percorso HTTP; usare un MCP client locale |
