<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime estensione VS Code

L’estensione VS Code è un launcher e una UI di comodità per lo stesso server `local-shell-mcp`. È una scelta di runtime perché avvia il processo server per il workspace corrente dell’editor.

Non è il connettore ChatGPT. Da web/app ChatGPT continua a collegarsi a un endpoint HTTPS pubblico `/mcp`.

## Cosa fa l’estensione

L’estensione:

- Avvia `local-shell-mcp` per il workspace VS Code corrente.
- Arresta e riavvia il server.
- Mostra il server output in un canale di output VS Code.
- Controlla `/healthz`.
- Copia l’URL MCP.
- Copia un ChatGPT setup prompt con workspace ed endpoint.

L’estensione non include il server binary. Installa `local-shell-mcp` separatamente e indica all’estensione l’executable se non è in `PATH`.

## Quando usarla

Usa questo runtime quando:

- Normalmente inizi da una cartella VS Code.
- Vuoi un flusso button/command palette invece di lanciare manualmente un terminal command.
- Il progetto ha già le dipendenze installate sul host.
- Lavori su repository fidati o un workspace ristretto.
- Sei disposto a esporre al modello solo quel workspace.

Usa Docker quando:

- Il repository non è fidato.
- Il task installerà package arbitrari.
- Serve un ampio toolchain preinstallato.
- Vuoi reset semplice ricreando un container.
- Vuoi un boundary più netto del tuo account host.

## Installare l’executable

Scegli un metodo di installazione del server:

```bash
pipx install local-shell-mcp
```

oppure scarica il release binary per il tuo OS e mettilo in `PATH`.

Poi installa l’asset VSIX della release:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

In alternativa usa **Extensions: Install from VSIX...** nella command palette.

## Impostazioni estensione

| Setting | Scopo | Valore tipico |
|---|---|---|
| `local-shell-mcp.executablePath` | Path del server executable | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Bind address del local server | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace esposto a MCP | Vuoto per la prima cartella VS Code o path esplicito |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin copiato nei prompt e URL | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN per OAuth authorization | Strong random value per uso pubblico |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Mantieni `false` per direct host usage |
| `local-shell-mcp.extraEnv` | Extra environment per server process | Solo project-specific safe values |

## Flusso base

1. Apri una cartella progetto in VS Code.
2. Esegui **local-shell-mcp: Start Server**.
3. Esegui **Show Server Status** o **Check Health** se disponibili.
4. Usa **Copy MCP URL** per un client locale o **Copy ChatGPT Setup Prompt** per ChatGPT.
5. Aggiungi l’endpoint al client.

Il local endpoint di solito è:

```text
http://127.0.0.1:8765/mcp
```

È utile per client locali ma non raggiungibile da ChatGPT web/app.

## Uso con ChatGPT

Per usare da ChatGPT un server avviato da VS Code, aggiungi HTTPS tunnel o reverse proxy davanti alla porta locale.

Forma di esempio:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Imposta:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

L’URL copiato per ChatGPT deve terminare con `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Sicurezza del runtime host

L’estensione di solito esegue commands come il tuo host user. È sostanzialmente diverso da un disposable Docker container.

Regole consigliate:

- Apri solo il repository che vuoi far controllare al modello.
- Mantieni `allowFullContainer` disabilitato.
- Non impostare workspace root sulla home directory.
- Non mantenere secrets non correlati nel workspace.
- Usa `secret_scan` prima di commit e push.
- Preferisci Docker per repository sconosciuti o task pesanti di installazione package.

## Prompt comune

Dopo aver copiato il setup prompt, inizia con un task read-only:

```text
Usa local-shell-mcp. Prima chiama environment_get e file_tree sul workspace. Non modificare ancora i file.
```

Poi passa a un edit circoscritto:

```text
Correggi il failing test in questo workspace. Leggi prima i file pertinenti, crea la patch minima, esegui il test mirato e mostra git diff. Non fare commit finché non approvo.
```

## Risoluzione problemi

| Sintomo | Controllo |
|---|---|
| L’estensione non avvia il server | Conferma che `local-shell-mcp.executablePath` esista e che `--help` funzioni in terminal |
| ChatGPT non riesce a raggiungerlo | Una URL locale `127.0.0.1` non è pubblica; configura tunnel/proxy e `publicBaseUrl` |
| I tool espongono la cartella sbagliata | Imposta esplicitamente `local-shell-mcp.workspaceRoot` |
| Auth fallisce dopo restart | Imposta OAuth admin PIN e JWT secret stabili tramite `extraEnv` o configurazione runtime |
| Ai commands mancano dipendenze | Installa dipendenze sul host o passa al runtime Docker |
