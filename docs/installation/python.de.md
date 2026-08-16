<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Python-, pipx- und Source-Runtimes

Python-Runtimes eignen sich für Entwicklung, Debugging und Umgebungen, in denen Python-Paketverwaltung einfacher als Docker ist. Sie führen denselben Server wie die Docker- und Binary-Runtimes aus.

Diese Seite behandelt drei verwandte Fälle:

- `pipx install local-shell-mcp`: Installation eines ausführbaren Programms auf Benutzerebene.
- `pip install local-shell-mcp`: Installation in einer vorhandenen virtuellen Umgebung.
- Editable source checkout: Entwicklung oder Debugging des Projekts selbst.

## pipx-Installation

`pipx` ist für normale Benutzer die sauberste Python-basierte Installation, da der Befehl seine eigene virtuelle Umgebung erhält und gleichzeitig ein ausführbares Programm in `PATH` bereitgestellt wird.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Starten Sie einen lokalen HTTP-MCP-Server:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Prüfen Sie den Zustand:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Installation in einer virtuellen Umgebung

Verwenden Sie dies, wenn Sie Python-Umgebungen bereits selbst verwalten:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Der Prozess verwendet die auf dem Host installierten Werkzeuge. Das Python-Paket installiert keine Compiler, Git, Browser-Systemabhängigkeiten oder Projektabhängigkeiten für Sie.

## Editable source checkout

Für die Projektentwicklung:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Prüfungen ausführen:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Browser-Einrichtung

Das Python-Paket hängt von Playwright ab, Browser-Binärdateien müssen auf dem Host jedoch möglicherweise zusätzlich installiert werden:

```bash
python -m playwright install chromium
```

Einige Linux-Hosts benötigen zusätzliche Browser-Abhängigkeiten. Docker vermeidet einen Großteil davon, weil das Image von einem Playwright-Basisimage ausgeht.

## Öffentliche HTTP-MCP-Nutzung

Für ChatGPT oder einen anderen öffentlichen HTTP-MCP-Client konfigurieren Sie dieselben Public-Origin- und OAuth-Einstellungen wie bei anderen HTTP-Runtimes und veröffentlichen den lokalen Port über Reverse Proxy oder Tunnel.

Der öffentliche MCP-Endpoint lautet:

```text
https://your-public-host.example.com/mcp
```

## Entwicklungsmodi

| Mode | Command | Verwendung |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | Vollständige MCP-Clients über HTTP, einschließlich ChatGPT hinter HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Diagnose- oder Kompatibilitäts-Endpunkte, nicht der Hauptpfad für ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | Lokale MCP-Clients, die den Prozess starten |

`mode=both` ist reserviert und sollte derzeit nicht als Modus eines einzelnen Prozesses verwendet werden.

## Sicherheit des Host-Runtime

Python-Installationen laufen als Ihr Host-Benutzer, sofern Sie sie nicht in eine VM oder einen Container legen. Halten Sie den Workspace eng, den Full-Container-Modus deaktiviert und richten Sie den Workspace nicht auf ein Home-Verzeichnis.

Verwenden Sie Docker Compose für nicht vertrauenswürdige Repositories, paketmanager-intensive Aufgaben oder Workflows, bei denen Zurücksetzbarkeit wichtiger als Host-Integration ist.
