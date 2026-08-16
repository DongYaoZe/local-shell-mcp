<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Scelte del runtime e modello di deployment

`local-shell-mcp` richiede due decisioni indipendenti:

1. **Runtime**: come viene eseguito il processo server e quale workspace controlla.
2. **Client connection**: come ChatGPT o un altro MCP client raggiunge quel server.

Non considerare ChatGPT un metodo di deployment. ChatGPT è un client. Docker, VS Code extension, release binaries, installazioni Python e stdio mode sono scelte di runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Una configurazione pubblica comune è:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Una configurazione con MCP client locale può essere più semplice:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Matrice di scelta del runtime

| Runtime | Ideale per | Confine di isolamento | Origine toolchain | Accesso pubblico ChatGPT | Pagina |
|---|---|---|---|---|---|
| Docker Compose | La maggior parte dei workload coding-agent e workspace riproducibili | Container | Project image con toolchain predefinito ampio | Aggiungi proxy HTTPS o tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Deployment pubblico in uno stack con Cloudflare Tunnel | Container | Project image | Integrato nel profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Avvio/arresto server da editor workspace | Di solito processo host | Strumenti host più executable configurato | Aggiungi tunnel/proxy HTTPS esterno per ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Host o VM senza Docker | Host or VM | Strumenti host più executable configurato | Aggiungi proxy HTTPS o tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Uso Python-native, debugging, development | Host virtualenv or VM | Package Python più strumenti host | Aggiungi proxy HTTPS o tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP client locali che avviano processi direttamente | Client process boundary | Strumenti host più executable configurato | Non utilizzabile da ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Matrice connessione client

| Percorso client | Richiede HTTPS pubblico | Usa `/mcp` | Richiede OAuth | Runtime tipico |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Sì | Sì | Sì per uso pubblico | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | No | No | No | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Di solito no su localhost; sì tra reti | Sì | Consigliato fuori da localhost | Any HTTP runtime |
| VS Code extension helper flow | Solo se ChatGPT deve collegarsi | Sì quando si copia URL ChatGPT | Consigliato per ChatGPT | VS Code-launched runtime |

Vedi [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Cosa controlla ogni runtime

Ogni runtime avvia lo stesso codice server ed espone le stesse famiglie di MCP tools quando abilitate:

- Shell e persistent shell sessions.
- Filesystem, search e patch tools.
- Operazioni Git.
- Browser automation tramite Playwright.
- Audit log e task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle e machine-routed tools.

La differenza non è l’API astratta ma l’**operating environment** dietro di essa.

| Domanda | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Dove vengono eseguiti i comandi? | Dentro il container | Di solito nel workspace host | Nell’ambiente di processo host o VM |
| Workspace predefinito? | Mounted `/workspace` | Cartella VS Code corrente o path configurato | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser preinstallati? | Sì, ampiamente | Solo se installati sul host | Solo se installati sul host |
| Facile da resettare? | Ricrea container e volume workspace | Dipende dal workspace | Dipende da host/VM |
| Adatto a installazioni arbitrarie? | Sì, se disposable | Più rischioso su host | Più rischioso fuori da VM |

## Selezione consigliata

Usa **Docker Compose** per primo salvo motivi contrari. Offre il confine di sicurezza più chiaro e il toolchain predefinito più completo.

Usa **VS Code extension** quando il workflow parte dall’editor e vuoi un launcher locale. È comunque un runtime. Da solo non rende il server raggiungibile da ChatGPT; per ChatGPT web/app aggiungi tunnel o reverse proxy.

Usa **standalone binary** quando Docker non è disponibile ma VM, container host o account dedicato forniscono già un confine.

Usa **`pipx` o source install** per development/debugging di `local-shell-mcp` o quando un ambiente Python è più facile da mantenere.

Usa **stdio mode** solo con MCP client locali che possono avviare il processo server. Non è un deployment pubblico e non è utilizzabile direttamente da ChatGPT web/app.

## Regola dell’endpoint pubblico

Per MCP client HTTP come ChatGPT, l’endpoint MCP è:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` contiene solo l’origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Non aggiungere `/mcp` a `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Pagine runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Pagine client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
