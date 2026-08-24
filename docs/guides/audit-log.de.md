<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
# Audit-Log

`local-shell-mcp` schreibt strukturierte Audit-Einträge, um nachvollziehen zu können, was ein verbundener client getan hat.

Standardpfad:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Was aufgezeichnet wird

Audit-Einträge erfassen unter anderem:

- Start/Ende von Tool Calls.
- Metadaten zur Befehlsausführung.
- Timeouts und behandelte Fehler.
- Registrierung von Remote-Workern und Job-Aktivität.
- Erstellung und Widerruf von File Links.
- Authentifizierungsbezogene Ereignisse, sofern relevant.

Sensible Argumente werden geschwärzt, wenn der Server sie erkennen kann.

## Log lesen

Verwenden Sie das MCP-Tool:

```text
audit_tail
```

Oder prüfen Sie die Datei direkt:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Operative Nutzung

Audit-Logs sind besonders nützlich zum:

- Prüfen von Befehlen, die Dateien verändert haben.
- Feststellen, ob ein Remote Worker verwendet wurde.
- Debuggen unerwarteter Fehler.
- Erkennen versehentlich veröffentlichter File Links.
- Unterstützen der Incident Response nach einem Fehler bei einer öffentlichen Bereitstellung.

## Aufbewahrung

Die aktive `audit.jsonl` ist standardmäßig durch `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` auf 20 MB begrenzt. Bei der Retention-Wartung werden ältere Einträge nicht verworfen, sondern in eigenständige Zstandard-Archive unter `audit-archive/*.jsonl.zst` verschoben. Ausgelagerte große audit payloads werden vor dem Bereinigen des Hot-Speichers ebenfalls in das Archiv aufgenommen.

Für komprimierte Archive gilt mit `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` ein separates Limit von standardmäßig 512 MB. Bei Überschreitung werden die ältesten Archive zuerst gelöscht. Mit `0` lässt sich die langfristige komprimierte Aufbewahrung deaktivieren. Web UI, Activity/Audit-Abfragen und `audit_tail` lesen ausschließlich das aktive Hot-Log. Komprimierte Archive dienen als Cold Storage für Aufbewahrung oder Export und werden bei normalen UI-Abfragen nicht automatisch dekomprimiert.

## Einschränkungen

Audit-Logs sind keine Sandbox. Sie unterstützen die Nachvollziehbarkeit, verhindern aber nicht, dass ein verbundenes Modell innerhalb seiner konfigurierten Befugnisse handelt.
