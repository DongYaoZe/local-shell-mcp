<!-- i18n-source-sha256: 8c683835be3adb3bf08d9d69b1731f61a39753bf255170fc663cf9456a0df54f -->
# Benutzeroberfläche

`local-shell-mcp` bietet zwei kompatible Benutzerschnittstellen über derselben Service-API, demselben Workspace, Persistent-Terminal-Register, Remote-Worker-Register und MCP-Audit-Log:

- **Web UI** ist ein natives Browser-Dashboard für schnelle Betriebsprüfungen.
- **OpenTUI** ist die vollständige terminalorientierte Anwendung und steht sowohl im Browser als auch als nativer Terminalbefehl zur Verfügung.

Keiner der Modi erzeugt eine separate Control Plane. Ein Wechsel der Oberfläche ändert keine verbundenen Maschinen, Sessions, Jobs, Berechtigungen oder Audit-Daten.

## Dienst starten

Starten Sie `local-shell-mcp` wie gewohnt:

```bash
local-shell-mcp --mode mcp
```

## ChatGPT Live Workspace

Wenn ChatGPT MCP Apps rendern kann, öffnet `workspace_open` eine schwebende kollaborative Ansicht für die aktuell angehängte logische Session. Die Session besitzt den dauerhaften Task-State; Live Workspace präsentiert nur Live-Aktivität und Human Controls. Daher setzt weder ein App-Reconnect noch ein Wechsel des ChatGPT/MCP-Transports die Session zurück.

Ein typischer Handoff sieht so aus:

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

`takeover=true` ersetzt einen noch aktiven älteren Agent-Run. Spätere Tool-Aufrufe des ersetzten Runs werden abgewiesen, bis dieser Agent die Session ausdrücklich erneut resumed. Sessions sind weder an machine noch working directory gebunden; normale Tool-Parameter wählen weiterhin lokale/remote Ziele und Pfade.

Ein optionaler `plan_manage`-Plan aktiviert Goal Mode für die Session. Ist der Plan aktiv und gibt es 15 Minuten keine Agent-Aktivität, kann ein angehängter Live Workspace ChatGPT zur Fortsetzung auffordern. Die Fortsetzung resumed zuerst dieselbe `session_id` und ist auf 10 Versuche begrenzt, akzeptiert oder abgelehnt. Blocked, completed und cancelled Plans werden nicht automatisch fortgesetzt; ein aktiver Plan mit ausschließlich completed/skipped Steps bleibt für eine Cleanup-Fortsetzung berechtigt, damit der resumed Agent den Plan finishen kann. Human pause/resume/cancel Controls aktualisieren den Session-owned Plan statt flüchtigen Live-Workspace-State.

## Browseroberfläche

Öffnen Sie:

```text
http://127.0.0.1:8765/ui
```

Für eine öffentliche Bereitstellung verwenden Sie den konfigurierten HTTPS-Origin:

```text
https://your-public-host.example.com/ui
```

Die Browseroberfläche verwendet denselben OAuth-Server und dieselben Scopes wie MCP. Seitengerüst und statische Assets sind öffentlich, damit der Login-Bildschirm geladen werden kann; `/api/ui/*` und der OpenTUI-Terminal-WebSocket bleiben geschützt. Zugriffstoken werden nur im Session Storage des Browsers gespeichert.

### Oberfläche wählen

Der OAuth-Bildschirm bietet zwei Einstiegspunkte:

- **Open Web UI** autorisiert und öffnet das native Dashboard.
- **Continue to OpenTUI** autorisiert und öffnet die Terminaloberfläche unter Beibehaltung des bisherigen Browserverhaltens.

Nach der Autorisierung kann der Umschalter in der Seitenleiste ohne erneute Anmeldung zwischen Web UI und OpenTUI wechseln. Die aktuelle native Seite wird beim vorübergehenden Wechsel zu OpenTUI gespeichert.

Die Routen können als Lesezeichen gespeichert werden:

```text
/ui/#/overview
/ui/#/machines
/ui/#/workloads
/ui/#/activity
/ui/#/console
```

`#/web` und `#/dashboard` sind Aliase für Overview. `#/tui` und `#/opentui` sind Aliase für Console.

## Native Web UI

Die native Web UI fragt die vorhandene Human-Interface-API alle fünf Sekunden ab und rendert browsernative Steuerelemente statt Terminalzellen. Ein PTY wird erst gestartet, wenn OpenTUI ausgewählt wurde.

### Overview

Overview zeigt die wichtigsten Betriebsinformationen zuerst:

- Zustand des Controllers und aktuelle LSM-Version.
- Anzahl der Online- und Offline-Maschinen.
- Aktive tracked Jobs und persistente Terminal-Sessions.
- CPU, Arbeitsspeicher, Workspace-Datenträger, Load, Netzwerkdurchsatz und Uptime.
- Warnungen aus worker-Status, Ressourcenschwellen, fehlgeschlagenen Jobs und fehlgeschlagenen MCP-Aufrufen.
- Letzte vom Modell ausgelöste MCP-Aktivität.

### Machines

Machines listet den lokalen Controller und verbundene Remote-worker mit Status, Plattform, Version, Arbeitsverzeichnis, Fähigkeiten und Last-seen-Informationen auf.

### Workloads

Workloads kombiniert aktive tracked Jobs und eigenständige persistente Shell-Sessions. In der Web UI sind diese Datensätze nur lesbar; für interaktive Sitzungsverwaltung verwenden Sie OpenTUI.

### Activity

Activity kombiniert aktuelle Warnungen mit jüngster MCP-Audit-Aktivität. Von Menschen eingegebene Befehle und Dateioperationen bleiben aus dem MCP-Audit-Log ausgeschlossen.

## OpenTUI im Browser

Durch Auswahl von **OpenTUI** wird dieselbe OpenTUI-Anwendung wie beim nativen Terminal-Launcher verzögert gestartet. Die Browserkonsole behält:

- Authentifizierten binären PTY-Transport über WebSocket.
- Automatische Terminalgrößenanpassung und Reconnect-Backoff.
- Mausinteraktion mit OpenTUI-Steuerelementen.
- Vollbildmodus und browsersichere Tastenkürzel.
- Mobile Schnellwahltasten und explizite Bildschirmtastatursteuerung.
- SIXEL- und Inline-image-Unterstützung über xterm.js.

Der Browser erstellt kein OpenTUI-PTY, solange der Benutzer im nativen Web-UI-Modus bleibt.

## Native OpenTUI

Eigenständige Release-Executables enthalten die plattformspezifische OpenTUI-Runtime. Behalten Sie nur die Hauptdatei, starten Sie den Dienst und führen Sie aus:

```bash
local-shell-mcp tui
```

Die native TUI verlangt vom menschlichen Bediener keine Anmeldung. Der Launcher übergibt transparent eine erzeugte lokale Berechtigung an die Loopback-API. Diese Berechtigung liegt im konfigurierten State Directory mit ausschließlich für den Eigentümer zugänglichen Rechten; ein Reverse Proxy, der über Loopback verbindet, erhält diesen Bypass nicht.

Ein Source-Checkout kann die TUI nach Installation der Bun-Abhängigkeiten ebenfalls ausführen:

```bash
cd ui
bun install --frozen-lockfile
bun run build
cd ..
local-shell-mcp tui
```

Verwenden Sie `--api-base` nur, wenn der lokale Dienst einen nicht standardmäßigen Port nutzt:

```bash
local-shell-mcp tui --api-base http://127.0.0.1:9876/api/ui
```

## OpenTUI-Bildschirme

### Dashboard

Dashboard ist die Betriebsübersicht von OpenTUI. Breite Terminals zeigen getrennte Bereiche für Node, Workload, Alert, Activity, Systeminformationen und Trends; schmalere Terminals fassen sie ohne horizontales Scrollen kompakt zusammen.

### Files

Files ist ein LSM-nativer Dateimanager mit drei Bereichen für lokale und entfernte Maschinen. Er unterstützt Erstellen, Bearbeiten, Umbenennen, Kopieren, Verschieben, Einfügen, Löschen, Umschalten versteckter Dateien, Aktualisieren, Textvorschau, Binärvorschau und begrenzte Bildminiaturen.

### Terminals

Terminals verwaltet persistente Shell-Sessions auf lokalen und entfernten Maschinen. Unterstützt werden vollständige Befehlseingabe, rohe interaktive Eingabe, Sitzungswechsel, Erstellung und Beendigung von Sessions, letzte Ausgabe sowie eine einklappbare MCP-Audit-Leiste.

### Audit

Audit liest das begrenzte JSONL-Audit-Log und unterstützt Filter nach Node, Operation, Event, Session, Search, Time-range und Sort sowie die Detailansicht einzelner Datensätze.

### Remotes

Remotes zeigt Online- und Offline-Remote-worker, Fähigkeiten, Arbeitsverzeichnisse und Systemmetadaten. Es kann eine einmalige Join-Einladung erzeugen, einen Node umbenennen oder seine persistente Identität widerrufen.

## OpenTUI-Navigation

Die obere Kategorienleiste und kontextbezogene Footer-Aktionen können sowohl in nativen Terminals als auch in der Browserkonsole mit der Maus angeklickt werden.

| Tasten | Aktion |
|---|---|
| `Alt+1` … `Alt+5` | Öffnet Dashboard, Files, Terminals, Remotes oder Audit. |
| `F2` … `F6` | Alternative Kategorie-Shortcuts. |
| `F1` | Tastaturhilfe öffnen. |
| `F9` | Maschinenliste aktualisieren. |
| `Alt+Q` | Nativen OpenTUI-Prozess beenden, ohne ein vom Browser reserviertes Ctrl-Kürzel auszulösen. |

Terminals verwendet `Alt+N` für eine neue Session, `Alt+W` zum Beenden der ausgewählten Session, `Alt+A` zum Umschalten der Audit-Leiste, `Alt+R` zum Aktualisieren und `Alt+Left/Right` zum Wechseln zwischen Sessions. Die Browserkonsole fängt diese Tastenkombinationen vor Browsernavigation oder Menüverarbeitung ab.

## Konfiguration

| YAML-Schlüssel | Umgebungsvariable | Standard | Zweck |
|---|---|---|---|
| `ui_enabled` | `LOCAL_SHELL_MCP_UI_ENABLED` | `true` | Benutzeroberflächen einbinden oder deaktivieren. |
| `ui_path` | `LOCAL_SHELL_MCP_UI_PATH` | `/ui` | Mount-Pfad der Browseroberfläche im MCP-Dienst. |
| `ui_tui_command` | `LOCAL_SHELL_MCP_UI_TUI_COMMAND` | auto | Auflösung des nativen OpenTUI-Executables überschreiben. |
| `ui_wallpaper` | `LOCAL_SHELL_MCP_UI_WALLPAPER` | `bing` | Hintergrund-Einstellung für OpenTUI-Browserkonsolen-Bereitstellungen. |
| `ui_terminal_idle_timeout_s` | `LOCAL_SHELL_MCP_UI_TERMINAL_IDLE_TIMEOUT_S` | `3600` | Inaktives Browser-OpenTUI-PTY nach dieser Sekundenzahl schließen; `0` deaktiviert das Timeout. |
| `ui_terminal_max_sessions` | `LOCAL_SHELL_MCP_UI_TERMINAL_MAX_SESSIONS` | `8` | Maximale Zahl gleichzeitiger Browser-OpenTUI-PTY-Sessions. |

## Hinweise zur Paketierung

- Docker-Images enthalten die Web-UI-Assets und die native OpenTUI-Runtime.
- Eigenständige Executables enthalten die Web-UI-Assets und eine komprimierte plattformspezifische OpenTUI-Runtime.
- Python-Wheels enthalten Browser-Assets; native OpenTUI benötigt ein Release-Executable oder einen Source-Checkout mit installierten Bun-Abhängigkeiten.
- Beide Oberflächen werden vom selben Prozess und Port wie MCP bereitgestellt; ein zusätzlicher Webdienst ist nicht erforderlich.
