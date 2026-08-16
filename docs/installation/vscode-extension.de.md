<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# VS-Code-Extension-Runtime

Die VS-Code-Extension ist Launcher und Komfort-UI für denselben `local-shell-mcp`-Server. Sie ist eine Runtime-Auswahl, weil sie den Serverprozess für den aktuellen Editor-Workspace startet.

Sie ist nicht der ChatGPT-Connector selbst. ChatGPT verbindet sich bei Nutzung aus web/app weiterhin mit einem öffentlichen HTTPS-Endpoint `/mcp`.

## Was die Extension tut

Die Extension:

- Startet `local-shell-mcp` für den aktuellen VS-Code-Workspace.
- Stoppt und startet den Server neu.
- Zeigt Server-Output in einem VS-Code-Output-Channel.
- Prüft `/healthz`.
- Kopiert die MCP-URL.
- Kopiert einen ChatGPT-Setup-Prompt mit Workspace und Endpoint.

Die Extension bündelt das Server-Binary nicht. Installieren Sie `local-shell-mcp` separat und konfigurieren Sie den Executable-Pfad, falls es nicht in `PATH` liegt.

## Wann verwenden

Verwenden Sie diesen Runtime, wenn:

- Sie meist mit einem VS-Code-Ordner beginnen.
- Sie Button/Command-Palette statt manuellem Terminalstart möchten.
- Projektabhängigkeiten bereits auf dem Host installiert sind.
- Sie mit vertrauenswürdigen Repositories oder engem Workspace arbeiten.
- Sie nur diesen Workspace dem Modell freigeben möchten.

Verwenden Sie Docker, wenn:

- Das Repository nicht vertrauenswürdig ist.
- Die Aufgabe beliebige Pakete installiert.
- Eine breite vorinstallierte Toolchain benötigt wird.
- Ein einfacher Reset durch Container-Neuerstellung gewünscht ist.
- Eine sauberere Grenze als das Hostkonto benötigt wird.

## Executable installieren

Wählen Sie eine Installationsmethode für den Server:

```bash
pipx install local-shell-mcp
```

oder laden Sie das Release-Binary für Ihr OS herunter und legen Sie es in `PATH`.

Installieren Sie danach das VSIX-Release-Asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Alternativ **Extensions: Install from VSIX...** in der Command Palette.

## Extension-Einstellungen

| Einstellung | Zweck | Typischer Wert |
|---|---|---|
| `local-shell-mcp.executablePath` | Pfad zum Server-Executable | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Bind-Adresse des lokalen Servers | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Lokaler Server-Port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace, der MCP bereitgestellt wird | Leer für ersten VS-Code-Ordner oder expliziter Pfad |
| `local-shell-mcp.authMode` | Authentifizierungsmodus | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Öffentlicher HTTPS-Origin für Prompts und URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN für OAuth-Autorisierung | Starker Zufallswert für öffentliche Nutzung |
| `local-shell-mcp.allowFullContainer` | Full-Container-Verhaltensflag | Für direkte Host-Nutzung `false` lassen |
| `local-shell-mcp.extraEnv` | Zusätzliche Environment-Werte für Serverprozess | Nur projektspezifische sichere Werte |

## Grundablauf

1. Öffnen Sie einen Projektordner in VS Code.
2. Führen Sie **local-shell-mcp: Start Server** aus.
3. Führen Sie **Show Server Status** oder **Check Health** aus, falls verfügbar.
4. Nutzen Sie **Copy MCP URL** für lokalen Client oder **Copy ChatGPT Setup Prompt** für ChatGPT.
5. Fügen Sie den Endpoint zum Client hinzu.

Der lokale Endpoint sieht meist so aus:

```text
http://127.0.0.1:8765/mcp
```

Er ist für lokale Clients nützlich, aber nicht von ChatGPT web/app erreichbar.

## Mit ChatGPT verwenden

Um einen von VS Code gestarteten Server mit ChatGPT zu verwenden, setzen Sie einen HTTPS-Tunnel oder Reverse Proxy vor den lokalen Port.

Beispielstruktur:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Setzen Sie:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

Die für ChatGPT kopierte URL muss mit `/mcp` enden:

```text
https://your-public-host.example.com/mcp
```

## Host-Runtime-Sicherheit

Die Extension führt Befehle meist als Host-Benutzer aus. Das unterscheidet sich wesentlich von einem disposable Docker-Container.

Empfohlene Regeln:

- Öffnen Sie nur das Repository, das das Modell kontrollieren soll.
- Lassen Sie `allowFullContainer` deaktiviert.
- Setzen Sie Workspace Root nicht auf Ihr Home-Verzeichnis.
- Bewahren Sie keine unbezogenen Secrets im Workspace auf.
- Verwenden Sie `secret_scan` vor Commits und Pushes.
- Bevorzugen Sie Docker für unbekannte Repositories oder paketinstallationslastige Aufgaben.

## Typischer Prompt

Beginnen Sie nach Kopieren des Setup-Prompts mit einer Read-only-Aufgabe:

```text
Verwende local-shell-mcp. Rufe zuerst environment_get und file_tree für den Workspace auf. Ändere noch keine Dateien.
```

Gehen Sie dann zu einer begrenzten Änderung über:

```text
Behebe den fehlgeschlagenen Test in diesem Workspace. Lies zuerst die relevanten Dateien, erstelle den kleinsten Patch, führe den Zieltest aus und zeige git diff. Committe erst nach meiner Freigabe.
```

## Fehlerbehebung

| Symptom | Prüfen |
|---|---|
| Extension kann Server nicht starten | Prüfen, ob `local-shell-mcp.executablePath` existiert und `--help` im Terminal läuft |
| ChatGPT kann ihn nicht erreichen | Lokale `127.0.0.1`-URL ist nicht öffentlich; Tunnel/Proxy und `publicBaseUrl` konfigurieren |
| Tools geben falschen Ordner frei | `local-shell-mcp.workspaceRoot` explizit setzen |
| Auth schlägt nach Neustart fehl | Stabile OAuth Admin PIN und JWT Secret über `extraEnv` oder Runtime-Konfiguration setzen |
| Befehlen fehlen Abhängigkeiten | Abhängigkeiten auf Host installieren oder zu Docker-Runtime wechseln |
