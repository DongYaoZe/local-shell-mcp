<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">Piano di controllo MCP compatibile con ChatGPT</span>

# local-shell-mcp

Dai al tuo assistente IA una shell controllata, un workspace reale, Git, browser automation, file sharing e accesso ai remote worker senza uscire dalla chat.

<div class="hero-actions" markdown>
[Inizia](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Scegli runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Riferimento strumenti](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Ambiente di coding reale
Esegui test, ispeziona repository, applica patch ai file, usa Git e conserva un audit trail da un unico MCP endpoint.
</div>

<div class="feature-card" markdown>
### Livelli runtime e client
Scegli un runtime come Docker, VS Code extension, binary, Python o stdio, poi collega separatamente ChatGPT o un altro MCP client.
</div>

<div class="feature-card" markdown>
### Controllo macchine remote
Collega macchine dietro NAT, firewall o HPC tramite connessioni worker in uscita senza aprire porte SSH.
</div>
</div>

## Cosa offre

`local-shell-mcp` espone un workspace locale o containerizzato controllato a ChatGPT e altri client MCP. Fornisce shell, shell persistente, filesystem, ricerca, patch, Git, Playwright, audit, Sessions logiche durevoli con Goal Plan opzionali, file link tokenizzati e strumenti remote worker tramite un server MCP compatibile con ChatGPT e OAuth.

Usalo quando l’IA deve ispezionare un repository, eseguire test, modificare file, usare Git, raccogliere browser evidence, produrre downloadable artifacts o controllare una macchina remota che può soltanto collegarsi in uscita al control server.

## Architettura

```text
Livello runtime: Docker / VS Code extension / binary / Python / stdio
Livello esposizione: localhost / HTTPS proxy / tunnel / stdio pipe
Livello client: ChatGPT / generic MCP client / editor helper
Workspace controllato: /workspace or configured workspace root
Remote worker opzionali: outbound machine connections
```

Il confine di isolamento previsto è il container o la VM che esegue il servizio.

## Inizia per scenario

| Scenario | Inizia qui | Perché |
|---|---|---|
| Primo deployment pubblico ChatGPT | [Quickstart](getting-started/quickstart.md) | Percorso Docker Compose con OAuth e setup `/mcp` |
| Scegliere il livello runtime | [Runtime choices](guides/deployment.md) | Spiega Docker, VS Code, binary, Python e stdio come opzioni runtime separate |
| Aggiungere ChatGPT come client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, primo prompt sicuro e tool discovery |
| Aggiungere LSM a DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Installare questo repository come bundle DSH mantenendo l’intera superficie LSM e remote workers |
| Eseguire da VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Runtime avviato dall’editor e note sulla sicurezza host |
| Imparare a usare il toolset | [Usage patterns](guides/usage-patterns.md) | Template di prompt e guida alla scelta degli strumenti |
| Capire ogni tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations e notes per ogni tool |
| Collegare HPC, NPU/GPU o server node | [Remote workers](guides/remote-workers.md) | Outbound worker join flow e remote tool usage |
| Condividere file generati | [File links](guides/file-links.md) | URL download tokenizzati con TTL e revoca |
| Rafforzare il deployment | [Security](security.md) | Isolamento, OAuth, workspace scope e audit logs |

## Principali famiglie di tool

| Famiglia | Esempi | Uso |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Build, test, script e processi lunghi |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Ispezione repository ed edit precisi |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Workflow source-control facilmente revisionabili |
| Sessions e goal | `session_manage`, `plan_manage` | Handoff durevole dei task, progress report e Goal mode opzionale |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Interazione persistente, UI check, screenshot, docs renderizzati e testo pagina |
| File links | `link_create`, `link_revoke` | Scaricare artefatti generati dalla chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Macchine dietro NAT, firewall o flussi di login cluster |

## Workflow tipici

### Coding con ChatGPT

1. Avvia un runtime come Docker Compose, VS Code extension, binary o Python in un workspace dedicato.
2. Esponi il runtime HTTP se ChatGPT necessita di network access.
3. Aggiungi il public `/mcp` endpoint a ChatGPT.
4. Chiedi prima di ispezionare il repository e fare check read-only.
5. Poi consenti patch ai file, test, review diff, commit e push quando approvati.
6. Controlla audit log quando il task coinvolge file link o sistemi remoti.

### Host HPC o acceleratore remoto

1. Crea un remote worker invite monouso.
2. Incolla il command generato sul remote host.
3. Usa tool normali con `machine`; Git via `run_shell` e transfer via `remote_transfer`.
4. Revoca il worker dopo il task.

### Generazione artefatti

1. Fai generare all’IA un file sotto `/workspace`.
2. Crea un tokenized file link con TTL/download limits.
3. Condividi il link in chat.
4. Revocalo al termine.

## Lingua

Questo site è costruito con il plugin i18n nativo di MkDocs. Usa il language selector nell’header per passare tra English e pagine tradotte. Le pagine senza traduzione fanno fallback a English.
