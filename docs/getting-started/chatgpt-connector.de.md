<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT-Connector

Diese Seite behandelt ChatGPT als Client-Verbindung. Sie wählt keinen Runtime aus. Starten Sie vor Verwendung dieser Seite den Server mit Docker, VS Code extension, einem Binary oder einer Python-Installation.

`local-shell-mcp` ist für ChatGPT Developer Mode und vollständige MCP-Clients ausgelegt. Der MCP-Endpoint stellt die normale LSM-Tool-Oberfläche direkt bereit.

## Runtime-Voraussetzungen

Wählen und starten Sie zuerst einen Runtime:

| Runtime | Seite |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Machen Sie diesen Runtime anschließend über einen Netzwerkpfad erreichbar, den ChatGPT erreichen kann. Siehe [network connectivity](../clients/connectivity.md).

## Öffentliche URL

ChatGPT muss den Server über HTTPS erreichen. Der MCP-Endpoint lautet:

```text
https://your-public-host.example.com/mcp
```

Stellen Sie sicher, dass `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` dem Public Origin entspricht:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Fügen Sie `/mcp` nicht in `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` ein.

## OAuth-Einrichtung

Empfohlene öffentliche Einstellungen:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access Tokens laufen standardmäßig nicht ab, da lange Coding-Sessions kurze Token-Laufzeiten überschreiten können. Widerrufen Sie Zugriff bei Bedarf durch Rotation des JWT Secret oder erneutes Deployment mit frischem Zustand.

## Connector hinzufügen

1. Öffnen Sie ChatGPT Connector- oder Developer-Mode-MCP-Einstellungen.
2. Fügen Sie einen Custom MCP Server hinzu.
3. Geben Sie die MCP-URL ein: `https://your-public-host.example.com/mcp`.
4. Schließen Sie OAuth ab.
5. Genehmigen Sie die Tool-Oberfläche.

## Live Workspace MCP App

ChatGPT-Clients mit MCP-Apps-Unterstützung können `local-shell-mcp` als interaktiven Execution Workspace darstellen. Lassen Sie ChatGPT den Live Workspace einmal öffnen, wenn Echtzeit-Sichtbarkeit oder menschliche Zusammenarbeit hilfreich ist; danach verbindet sich die App selbst wieder, statt wiederholt `workspace_open` aufzurufen.

Live Workspace ist bewusst vom Reasoning des Modells getrennt. Er zeigt beobachtbaren Execution State und gemeinsame Resources:

- **Activity** zeigt Start, Abschluss und Fehler von MCP-Tools sowie menschliche Aktionen.
- **Terminal** verbindet sich mit dem bestehenden Persistent-Shell-Backend und zeigt Live-PTY-Ausgabe.
- **Files** durchsucht, zeigt, bearbeitet, erstellt und löscht lokale oder entfernte Workspace-Dateien.
- **Diff** zeigt staged und unstaged Git-Änderungen und kann den aktuellen Diff zur Prüfung an ChatGPT zurücksenden.
- **Jobs** zeigt verwaltete Jobs und persistente Sessions.
- **Remotes** zeigt Workers und bietet Einladen, Umbenennen und Widerrufen, wenn Remote-Support aktiv ist.
- **Audit** zeigt aktuelle strukturierte MCP-Audit-Einträge.

Live Workspace ist immer kollaborativ: ChatGPT und Mensch können denselben Workspace gleichzeitig ändern. Wenn der Host es unterstützt, öffnet er sich als schwebendes PiP-Fenster und kann zwischen Fullscreen und Fenster umgeschaltet werden. Es gibt keinen separaten Observe/Takeover-Zustand.

File-, Diff-, Audit- und Activity-Ansichten können ausgewählten Operational Context über die MCP-Apps-Bridge an den nächsten Modellturn senden. Dies ist explizit geteilter Kontext; die UI legt privates Model Reasoning weder offen noch rekonstruiert es.

### Netzwerk und Sicherheit

Die gerenderte MCP App verbindet sich aus ihrer Sandbox direkt mit dem konfigurierten Service Origin, um Terminal- und Event-Traffic mit geringer Latenz zu ermöglichen. Daher muss `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` der HTTPS-Origin sein, den der ChatGPT-Browser erreichen kann. Der MCP-Endpoint bleibt `https://your-public-host.example.com/mcp`.

Beim Öffnen des Workspace wird ein zufälliges, kurzlebiges Live-Workspace-Bearer-Token ausgegeben. Das Token erscheint nur in MCP-result metadata für die gerenderte App, nicht in model-visible structured content, und wird nur von den human/live-UI-APIs akzeptiert. Automatisches Wiederanheften an dieselbe `live_id` nutzt die aktuelle Credential erneut, sodass reconnecting Views einander nicht ungültig machen; außerdem wird die aktuelle logische `session_id` mitgeführt, damit die View ihre dauerhafte Session auch dann wiederherstellen kann, wenn der In-Memory-Live-Workspace-State verloren ging. Ein expliziter neuer `workspace_open`-Aufruf rotiert die Credential. Die eingebettete App verwendet weder Browser-Cookies noch Ambient Credentials.

Clients ohne MCP Apps können UI-Metadata ignorieren. Alle normalen MCP-Datentools bleiben verfügbar und verhalten sich unverändert.

## Erster Prompt

```text
Verwende local-shell-mcp. Rufe zuerst environment_get auf und liste dann die Workspace-Wurzel. Ändere noch keine Dateien.
```

Damit wird die Verbindung ohne Änderungen geprüft.

## Empfohlene Betriebsregeln

Geben Sie dem Modell klare Grenzen:

- Innerhalb von `/workspace` arbeiten, sofern nichts anderes ausdrücklich verlangt wird.
- Tests vor Commit ausführen.
- Vor Push `secret_scan` verwenden.
- `link_create` nur für sicher teilbare Dateien verwenden.
- Für lang laufende Prozesse persistente Shell-Sessions bevorzugen.
- Alle Befehle zusammenfassen, die Dateien geändert haben.

## Probleme bei der Tool-Erkennung

Wenn ChatGPT sich authentifizieren kann, aber erwartete Tools fehlen:

- Prüfen Sie, dass der Endpoint mit `/mcp` endet.
- Prüfen Sie `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Prüfen Sie Reverse-Proxy-Header und Request-Body-Limits.
- Prüfen Sie `docker compose logs --tail=200 local-shell-mcp`.
- Bestätigen Sie, dass der Service im Modus `mcp` oder `both` läuft.

## Sicherheitshinweise

Öffentliche Deployments müssen OAuth aktiviert lassen. Stellen Sie vollständige MCP-Tools niemals unauthentifiziert im öffentlichen Internet bereit. Behandeln Sie jedes genehmigte Tool als Teil der effektiven Berechtigung des verbundenen Modells.
