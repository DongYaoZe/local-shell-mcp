<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Runtime-Auswahl und Bereitstellungsmodell

Bei `local-shell-mcp` gibt es zwei unabhängige Entscheidungen:

1. **Runtime**: wie der Serverprozess läuft und welchen Workspace er kontrolliert.
2. **Client connection**: wie ChatGPT oder ein anderer MCP-Client diesen Server erreicht.

Behandeln Sie ChatGPT nicht als Deployment-Methode. ChatGPT ist ein Client. Docker, VS Code extension, Release-Binaries, Python-Installationen und stdio mode sind Runtime-Auswahlen.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Eine typische öffentliche Einrichtung ist:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Eine lokale MCP-Client-Einrichtung kann einfacher sein:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Runtime-Auswahlmatrix

| Runtime | Am besten für | Isolationsgrenze | Toolchain-Quelle | Öffentlicher ChatGPT-Zugriff | Seite |
|---|---|---|---|---|---|
| Docker Compose | Die meisten Coding-Agent-Workloads und reproduzierbare Workspaces | Container | Projektimage enthält breite Standard-Toolchain | HTTPS-Proxy oder Tunnel hinzufügen | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Ein-Stack-Public-Deployment mit Cloudflare Tunnel | Container | Project image | Im Compose-Profil `tunnel` integriert | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Server aus Editor-Workspace starten/stoppen | Meist Hostprozess | Hosttools plus konfiguriertes Executable | Externen HTTPS-Tunnel/Proxy für ChatGPT hinzufügen | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts oder VMs ohne Docker | Host or VM | Hosttools plus konfiguriertes Executable | HTTPS-Proxy oder Tunnel hinzufügen | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native Nutzung, Debugging, Entwicklung | Host virtualenv or VM | Python-Package plus Hosttools | HTTPS-Proxy oder Tunnel hinzufügen | [Python install](../installation/python.md) |
| Stdio mode | Lokale MCP-Clients, die Prozesse direkt starten | Client process boundary | Hosttools plus konfiguriertes Executable | Nicht mit ChatGPT web/app nutzbar | [Stdio mode](../installation/stdio.md) |

## Client-Verbindungsmatrix

| Client-Pfad | Öffentliches HTTPS nötig | Nutzt `/mcp` | OAuth nötig | Typischer Runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Ja | Ja | Ja für öffentliche Nutzung | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Nein | Nein | Nein | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Für localhost meist nein; über Netzwerke ja | Ja | Außerhalb localhost empfohlen | Any HTTP runtime |
| VS Code extension helper flow | Nur wenn ChatGPT verbinden muss | Ja beim Kopieren der ChatGPT-URL | Für ChatGPT empfohlen | VS Code-launched runtime |

Siehe [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Was jeder Runtime kontrolliert

Jeder Runtime startet denselben Servercode und stellt bei Aktivierung dieselben MCP-Toolfamilien bereit:

- Shell und persistente Shell-Sessions.
- Filesystem-, Search- und Patch-Tools.
- Git-Operationen.
- Browser-Automatisierung über Playwright.
- Audit-Log und Task-State-Tools.
- Tokenisierte File Links.
- Optionale Remote-worker-Lifecycle- und Machine-routed-Tools.

Der Unterschied ist nicht die abstrakte API, sondern die **Betriebsumgebung** dahinter.

| Frage | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Wo laufen Befehle? | Im Container | Meist im Host-Workspace | In Host- oder VM-Prozessumgebung |
| Standard-Workspace? | Mounted `/workspace` | Aktueller VS-Code-Ordner oder konfigurierter Pfad | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/Browser vorinstalliert? | Weitgehend ja | Nur wenn auf Host installiert | Nur wenn auf Host installiert |
| Leicht zurücksetzbar? | Container und Workspace-Volume neu erstellen | Hängt vom Workspace ab | Hängt von Host/VM ab |
| Für beliebige Paketinstallationen geeignet? | Ja, wenn disposable | Riskanter auf Host | Riskanter außerhalb VM |

## Empfohlene Auswahl

Verwenden Sie zuerst **Docker Compose**, sofern kein Grund dagegen spricht. Es bietet die klarste Sicherheitsgrenze und die vollständigste Standard-Toolchain.

Verwenden Sie **VS Code extension**, wenn der Workflow im Editor beginnt und Sie einen lokalen Launcher möchten. Sie ist weiterhin ein Runtime. Sie macht den Server nicht von selbst für ChatGPT erreichbar; für ChatGPT web/app ist ein Tunnel oder Reverse Proxy nötig.

Verwenden Sie **standalone binary**, wenn Docker nicht verfügbar ist, aber VM, Container-Host oder dediziertes Benutzerkonto bereits eine Grenze bieten.

Verwenden Sie **`pipx` oder source install** für Entwicklung/Debugging von `local-shell-mcp` oder wenn eine Python-Umgebung leichter zu pflegen ist.

Verwenden Sie **stdio mode** nur für lokale MCP-Clients, die den Serverprozess starten können. Es ist kein öffentliches Deployment und nicht direkt mit ChatGPT web/app nutzbar.

## Regel für öffentlichen Endpoint

Für HTTP-MCP-Clients wie ChatGPT lautet der MCP-Endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` ist nur der Origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Hängen Sie `/mcp` nicht an `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` an.

## Runtime-Seiten

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Client-Seiten

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
