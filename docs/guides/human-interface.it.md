<!-- i18n-source-sha256: 8c683835be3adb3bf08d9d69b1731f61a39753bf255170fc663cf9456a0df54f -->
# Interfaccia umana

`local-shell-mcp` offre due interfacce umane compatibili sopra la stessa API del servizio, workspace, registro dei terminali persistenti, registro dei worker remoti e log di audit MCP:

- **Web UI** è una dashboard nativa del browser ottimizzata per una rapida ispezione operativa.
- **OpenTUI** è l’applicazione completa orientata al terminale ed è disponibile sia nel browser sia come comando terminale nativo.

Nessuna modalità crea un control plane separato. Cambiare interfaccia non modifica macchine connesse, Sessions, jobs, permessi o dati di audit.

## Avviare il servizio

Avvia `local-shell-mcp` normalmente:

```bash
local-shell-mcp --mode mcp
```

## Live Workspace di ChatGPT

Quando ChatGPT può renderizzare MCP Apps, `workspace_open` apre una view collaborativa flottante per la Session logica attualmente collegata. La Session possiede lo stato durevole del task; Live Workspace presenta soltanto attività live e controlli umani. Perciò una riconnessione dell’app o un cambio del trasporto ChatGPT/MCP non resetta la Session.

Un handoff tipico è:

```text
session_manage(action="start", objective=...)
        -> session_id
... tool work + session_manage(action="report", ...) ...
new agent run
session_manage(action="resume", session_id=..., takeover=true)
        -> inherited progress, Plan, and recent activity
workspace_open()
        -> reconnectable view of that Session
```

`takeover=true` sostituisce un vecchio agent run ancora attivo. Ogni successiva tool call dal run sostituito viene rifiutata finché quell’agente non esegue di nuovo resume esplicito della Session. Le Sessions non sono legate a machine o working directory; i normali parametri degli strumenti continuano a scegliere target local/remote e path.

Un Plan opzionale `plan_manage` abilita Goal mode per la Session. Se il Plan è active e non c’è attività dell’agente per 15 minuti, un Live Workspace collegato può chiedere a ChatGPT di continuare. La continuazione esegue prima resume dello stesso `session_id` ed è limitata a 10 tentativi, accettati o rifiutati. I Plan blocked, completed o cancelled non continuano automaticamente; un Plan active con tutti gli step completed/skipped resta eleggibile per una continuazione di cleanup affinché l’agente ripreso possa finish il Plan. I controlli umani pause/resume/cancel aggiornano il Plan della Session, non stato Live Workspace effimero.

## Interfaccia browser

Apri:

```text
http://127.0.0.1:8765/ui
```

Per un deployment pubblico, usa l’origin HTTPS configurata:

```text
https://your-public-host.example.com/ui
```

L’interfaccia browser usa lo stesso server OAuth e gli stessi scope di MCP. La shell della pagina e gli asset statici sono pubblici per consentire il caricamento della schermata di login, mentre `/api/ui/*` e il WebSocket del terminale OpenTUI restano protetti. I token di accesso sono conservati solo nel session storage del browser.

### Scegliere un’interfaccia

La schermata OAuth offre due punti di ingresso:

- **Open Web UI** autorizza e apre la dashboard nativa.
- **Continue to OpenTUI** autorizza e apre l’interfaccia terminale, mantenendo il precedente comportamento del browser.

Dopo l’autorizzazione, il selettore nella barra laterale passa tra Web UI e OpenTUI senza un nuovo login. La pagina nativa corrente viene ricordata quando si passa temporaneamente a OpenTUI.

Le route sono aggiungibili ai preferiti:

```text
/ui/#/overview
/ui/#/machines
/ui/#/workloads
/ui/#/activity
/ui/#/console
```

`#/web` e `#/dashboard` sono alias di Overview. `#/tui` e `#/opentui` sono alias di Console.

## Web UI nativa

La Web UI nativa interroga l’API esistente dell’interfaccia umana ogni cinque secondi e rende controlli nativi del browser invece di celle di terminale. Non avvia un PTY finché non viene selezionato OpenTUI.

### Overview

Overview mostra per prime le informazioni operative più importanti:

- Stato del controller e versione LSM corrente.
- Numero di macchine online e offline.
- Tracked job attivi e sessioni terminale persistenti.
- CPU, memoria, disco del workspace, load, throughput di rete e uptime.
- Avvisi generati dallo stato dei worker, soglie delle risorse, job falliti e chiamate MCP fallite.
- Attività MCP recente avviata dal modello.

### Machines

Machines elenca il controller locale e i worker remoti connessi con stato, piattaforma, versione, directory di lavoro, capacità e informazioni last-seen.

### Workloads

Workloads combina tracked job attivi e sessioni shell persistenti autonome. La Web UI resta in sola lettura per questi record; usa OpenTUI per la gestione interattiva delle sessioni.

### Activity

Activity combina gli avvisi correnti con la recente attività di audit MCP. I comandi e le operazioni sui file inseriti da persone restano esclusi dal log di audit MCP.

## OpenTUI nel browser

Selezionando **OpenTUI** viene avviata on demand la stessa applicazione OpenTUI usata dal launcher terminale nativo. La console browser mantiene:

- Trasporto PTY binario autenticato via WebSocket.
- Ridimensionamento automatico del terminale e backoff di riconnessione.
- Interazione mouse con i controlli OpenTUI.
- Modalità a schermo intero e scorciatoie da tastiera sicure per il browser.
- Tasti rapidi mobile e controllo esplicito della tastiera software.
- Supporto SIXEL e inline image tramite xterm.js.

Il browser non crea un PTY OpenTUI finché l’utente resta nella modalità Web UI nativa.

## OpenTUI nativo

Gli eseguibili release standalone incorporano il runtime OpenTUI della piattaforma. Mantieni solo l’eseguibile principale, avvia il servizio e poi esegui:

```bash
local-shell-mcp tui
```

Il TUI nativo non richiede login all’operatore umano. Il launcher fornisce in modo trasparente una credenziale locale generata all’API loopback. La credenziale è archiviata nello state directory configurato con permessi riservati al proprietario; un reverse proxy connesso da loopback non riceve questo bypass.

Un checkout sorgente può eseguire il TUI dopo aver installato le dipendenze Bun:

```bash
cd ui
bun install --frozen-lockfile
bun run build
cd ..
local-shell-mcp tui
```

Usa `--api-base` solo quando il servizio locale usa una porta non predefinita:

```bash
local-shell-mcp tui --api-base http://127.0.0.1:9876/api/ui
```

## Schermate OpenTUI

### Dashboard

Dashboard è la panoramica operativa di OpenTUI. I terminali larghi mostrano regioni separate per node, workload, alert, activity, informazioni di sistema e trend; quelli più stretti le comprimono in riepiloghi compatti senza scorrimento orizzontale.

### Files

Files è un file manager nativo LSM a tre pannelli per macchine locali e remote. Offre creazione, modifica, rinomina, copia, spostamento, incolla, eliminazione, toggle dei file nascosti, refresh, anteprima testo, anteprima binaria e miniature di immagini limitate.

### Terminals

Terminals gestisce sessioni shell persistenti su macchine locali e remote. Supporta input di comandi completi, input interattivo raw, cambio sessione, creazione e terminazione sessioni, output recente e un pannello audit MCP comprimibile.

### Audit

Audit legge il log di audit JSONL limitato e supporta filtri node, operation, event, session, search, time-range e sort, oltre all’ispezione dei dettagli dei record.

### Remotes

Remotes mostra worker remoti online e offline, capacità, directory di lavoro e metadati di sistema. Può creare un join invite monouso, rinominare un node o revocarne l’identità persistente.

## Navigazione OpenTUI

La barra delle categorie in alto e le azioni contestuali nel footer sono cliccabili con il mouse sia nei terminali nativi sia nella console browser.

| Tasti | Azione |
|---|---|
| `Alt+1` … `Alt+5` | Apre Dashboard, Files, Terminals, Remotes o Audit. |
| `F2` … `F6` | Shortcut alternativi di categoria. |
| `F1` | Apri la guida della tastiera. |
| `F9` | Aggiorna l’elenco macchine. |
| `Alt+Q` | Esci dal processo OpenTUI nativo senza attivare una scorciatoia Ctrl riservata dal browser. |

Terminals usa `Alt+N` per una nuova sessione, `Alt+W` per terminare quella selezionata, `Alt+A` per attivare il pannello audit, `Alt+R` per aggiornare e `Alt+Left/Right` per cambiare sessione. La console browser intercetta queste combinazioni prima della navigazione o dei menu del browser.

## Configurazione

| Chiave YAML | Variabile d’ambiente | Default | Scopo |
|---|---|---|---|
| `ui_enabled` | `LOCAL_SHELL_MCP_UI_ENABLED` | `true` | Monta o disabilita le interfacce umane. |
| `ui_path` | `LOCAL_SHELL_MCP_UI_PATH` | `/ui` | Percorso di mount dell’interfaccia browser sul servizio MCP. |
| `ui_tui_command` | `LOCAL_SHELL_MCP_UI_TUI_COMMAND` | auto | Sovrascrive la risoluzione dell’eseguibile OpenTUI nativo. |
| `ui_wallpaper` | `LOCAL_SHELL_MCP_UI_WALLPAPER` | `bing` | Impostazione sfondo mantenuta per deployment della console OpenTUI nel browser. |
| `ui_terminal_idle_timeout_s` | `LOCAL_SHELL_MCP_UI_TERMINAL_IDLE_TIMEOUT_S` | `3600` | Chiude un PTY OpenTUI browser inattivo dopo questi secondi; `0` disabilita il timeout. |
| `ui_terminal_max_sessions` | `LOCAL_SHELL_MCP_UI_TERMINAL_MAX_SESSIONS` | `8` | Numero massimo di sessioni PTY OpenTUI browser contemporanee. |

## Note di packaging

- Le immagini Docker includono gli asset Web UI e il runtime OpenTUI nativo.
- Gli eseguibili standalone incorporano gli asset Web UI e un runtime OpenTUI di piattaforma compresso.
- I wheel Python includono gli asset browser; OpenTUI nativo richiede un eseguibile release o un checkout sorgente con le dipendenze Bun installate.
- Entrambe le interfacce sono servite dallo stesso processo e porta di MCP; non è necessario alcun servizio web aggiuntivo.
