<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Dateilinks

`local-shell-mcp` kann Dateien aus dem kontrollierten Workspace über hochentropische Bearer-URLs bereitstellen. Das ist nützlich, wenn die KI Berichte, Archive, PDFs, Screenshots oder andere Artefakte erzeugt, die im Chat heruntergeladen oder angezeigt werden sollen.

## Wann Dateilinks sinnvoll sind

Verwenden Sie Dateilinks für:

- Generierte PDFs oder Berichte.
- Screenshots und Browser-Artefakte.
- Build-Ausgaben.
- Logs, die zu groß zum Einfügen sind.
- Archive zur manuellen Prüfung.

Verwenden Sie Dateilinks nicht für Secrets, Private Keys, Credential-Speicher oder unrelated personenbezogene Daten.

## Typischer Ablauf

1. Erzeugen oder finden Sie eine Datei unter `/workspace`.
2. Rufen Sie `link_create` mit TTL und optionalem Download-Limit auf. Setzen Sie `inline=true`, wenn die Datei direkt im Browser oder als Markdown-Bild gerendert werden soll; Standard ist `false`, wodurch ein Attachment-Download erzwungen wird.
3. Teilen Sie die zurückgegebene URL.
4. Widerrufen Sie den Link, sobald er nicht mehr benötigt wird.

## Relevante Tools

| Tool | Zweck |
|---|---|
| `link_create` | Tokenisierte URL für eine Workspace-Datei erstellen. |
| `link_list` | Aktive Links anzeigen. |
| `link_revoke` | Einen Link vor Ablauf deaktivieren. |

## Steuerung

Zu den Konfigurationsoptionen gehören:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Verwenden Sie für sensible Artefakte kürzere TTLs und setzen Sie ein maximales Download-Limit, wenn ein Link für einen einzigen Empfänger bestimmt ist.

## Sicherheitshinweise

Dateilinks sind Bearer-URLs. Jeder mit der URL kann die Datei herunterladen, bis sie abläuft, das Download-Limit erreicht oder der Link widerrufen wird. Behandeln Sie sie wie temporäre Secrets. Inline-Antworten enthalten eine CSP-Sandbox und `X-Content-Type-Options: nosniff`, sodass aktive Formate nicht auf den LSM-Origin zugreifen oder als unsandboxed same-origin content ausgeführt werden können.
