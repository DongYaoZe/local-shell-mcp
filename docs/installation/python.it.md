<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Runtime Python, pipx e source

I runtime Python sono utili per sviluppo, debug e ambienti in cui la gestione dei pacchetti Python è più semplice di Docker. Eseguono lo stesso server dei runtime Docker e binary.

Usa questa pagina per tre casi correlati:

- `pipx install local-shell-mcp`: installazione di executable a livello utente.
- `pip install local-shell-mcp`: installazione in un virtual environment esistente.
- Editable source checkout: sviluppare o eseguire il debug del progetto stesso.

## Installazione pipx

`pipx` è l’installazione basata su Python più pulita per utenti normali, perché assegna al comando un proprio virtual environment esponendo al contempo un executable nel `PATH`.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Avvia un server MCP HTTP locale:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Controlla lo stato:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Installazione in virtual environment

Usa questa opzione se gestisci già manualmente gli ambienti Python:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Il process usa gli strumenti installati sull’host. Il pacchetto Python non installa per te compilatori, Git, dipendenze di sistema del browser o dipendenze del progetto.

## Editable source checkout

Usa per lo sviluppo del progetto:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Esegui i controlli:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Configurazione browser

Il pacchetto Python dipende da Playwright, ma i browser binaries potrebbero dover essere installati separatamente sull’host:

```bash
python -m playwright install chromium
```

Alcuni host Linux richiedono dipendenze browser aggiuntive. Docker evita gran parte di questo perché l’immagine parte da una Playwright base image.

## Uso pubblico HTTP MCP

Per ChatGPT o un altro public HTTP MCP client, configura le stesse impostazioni public origin e OAuth degli altri runtime HTTP, quindi esponi la porta locale tramite reverse proxy o tunnel.

L’endpoint MCP pubblico è:

```text
https://your-public-host.example.com/mcp
```

## Modalità di sviluppo

| Mode | Command | Uso |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | MCP client completi via HTTP, incluso ChatGPT dietro HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Endpoint diagnostici o di compatibilità, non il percorso principale di ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | MCP client locali che avviano il process |

`mode=both` è riservato e attualmente non dovrebbe essere usato come mode di un singolo process.

## Sicurezza del host runtime

Le installazioni Python vengono eseguite come il tuo host user, salvo che siano poste in VM/container. Mantieni il workspace ristretto, full-container mode disabilitato e non puntare il workspace a un home directory.

Usa Docker Compose per repositories non attendibili, task intensivi di package manager o workflow in cui resetability conta più dell’integrazione con l’host.
