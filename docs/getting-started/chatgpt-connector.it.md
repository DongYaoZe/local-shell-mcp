<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Connettore ChatGPT

Questa pagina tratta ChatGPT come connessione client. Non sceglie il runtime. Prima di usarla, avvia il server con Docker, VS Code extension, un binary o un’installazione Python.

`local-shell-mcp` è progettato per ChatGPT Developer Mode e client MCP completi. L’endpoint MCP espone direttamente la normale superficie degli strumenti LSM.

## Prerequisiti del runtime

Scegli e avvia prima un runtime:

| Runtime | Pagina |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Poi esponi quel runtime tramite un percorso di rete raggiungibile da ChatGPT. Vedi [network connectivity](../clients/connectivity.md).

## URL pubblico

ChatGPT deve raggiungere il server via HTTPS. L’endpoint MCP è:

```text
https://your-public-host.example.com/mcp
```

Assicurati che `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` corrisponda al public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Non includere `/mcp` in `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Configurazione OAuth

Impostazioni pubbliche consigliate:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Gli access token non scadono per impostazione predefinita perché le sessioni di coding lunghe possono superare lifetime brevi dei token. Revoca l’accesso ruotando il JWT secret o facendo un nuovo deployment con stato pulito quando necessario.

## Aggiungere il connettore

1. Apri le impostazioni del connector o Developer Mode MCP di ChatGPT.
2. Aggiungi un custom MCP server.
3. Inserisci l’URL MCP: `https://your-public-host.example.com/mcp`.
4. Completa OAuth.
5. Approva la superficie degli strumenti.

## Live Workspace MCP App

I client ChatGPT con supporto MCP Apps possono renderizzare `local-shell-mcp` come execution workspace interattivo. Chiedi a ChatGPT di aprire Live Workspace una volta quando sono utili visibilità in tempo reale o collaborazione umana; poi l’app si riconnette da sola senza chiamate ripetute a `workspace_open`.

Live Workspace è intenzionalmente separato dal reasoning del modello. Mostra execution state osservabile e resources condivise:

- **Activity** mostra avvii, completamenti e fallimenti degli strumenti MCP e azioni umane.
- **Terminal** si collega al backend shell persistente esistente con output PTY live.
- **Files** esplora, visualizza, modifica, crea ed elimina file workspace locali o remoti.
- **Diff** mostra modifiche Git staged e unstaged e può inviare il diff corrente a ChatGPT per la revisione.
- **Jobs** mostra job gestiti e sessioni persistenti.
- **Remotes** mostra worker e fornisce azioni di invito, rinomina e revoca quando il supporto remoto è abilitato.
- **Audit** espone record strutturati recenti dell’audit MCP.

Live Workspace è sempre collaborative: ChatGPT e l’utente possono modificare contemporaneamente lo stesso workspace. Quando il host lo supporta, si apre come finestra flottante stile PiP e può passare tra fullscreen e finestra. Non esiste uno stato observe/takeover separato.

Le view files, diff, audit e activity possono inviare operational context selezionato al turno successivo del modello tramite il bridge MCP Apps. È contesto condiviso esplicito; la UI non espone né ricostruisce il reasoning privato del modello.

### Rete e sicurezza

La MCP App renderizzata si collega direttamente dal proprio sandbox al service origin configurato per traffico terminal/eventi a bassa latenza. Pertanto `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` deve essere l’origin HTTPS raggiungibile dal browser ChatGPT. L’endpoint MCP resta `https://your-public-host.example.com/mcp`.

L’apertura del workspace emette un bearer token Live Workspace casuale e di breve durata. Il token compare solo nei metadata del risultato MCP destinati all’app renderizzata, non entra nello structured content visibile al modello ed è accettato solo dalle API human/live UI. Il riaggancio automatico allo stesso `live_id` riutilizza la credential corrente così che le view in riconnessione non si invalidino a vicenda; trasporta anche il `session_id` logico corrente, consentendo di recuperare la Session durevole anche se lo stato Live Workspace in memoria è stato perso. Una nuova chiamata esplicita a `workspace_open` ruota la credential. L’app incorporata non usa cookie del browser o ambient credentials.

I client che non implementano MCP Apps possono ignorare i metadata UI. Tutti i normali strumenti dati MCP restano disponibili con lo stesso comportamento.

## Primo prompt

```text
Usa local-shell-mcp. Prima chiama environment_get, poi elenca la radice del workspace. Non modificare ancora i file.
```

Questo verifica la connettività senza effettuare modifiche.

## Regole operative consigliate

Dai al modello vincoli chiari:

- Lavora dentro `/workspace` salvo istruzioni esplicite diverse.
- Esegui i test prima del commit.
- Usa `secret_scan` prima del push.
- Usa `link_create` solo per file sicuri da condividere.
- Preferisci sessioni shell persistenti per processi lunghi.
- Riassumi tutti i comandi che hanno modificato file.

## Problemi di discovery degli strumenti

Se ChatGPT si autentica ma non mostra gli strumenti attesi:

- Conferma che l’endpoint termini con `/mcp`.
- Controlla `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Controlla gli header del reverse proxy e i limiti request body.
- Ispeziona `docker compose logs --tail=200 local-shell-mcp`.
- Conferma che il servizio sia in modalità `mcp` o `both`.

## Note di sicurezza

I deployment pubblici devono mantenere OAuth abilitato. Non esporre strumenti MCP completi senza autenticazione su Internet pubblico. Considera ogni strumento approvato parte dell’autorità effettiva del modello connesso.
