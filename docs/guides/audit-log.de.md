<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Das Log ist durch `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` begrenzt. Rotieren oder exportieren Sie es extern, wenn Sie eine längere Aufbewahrung benötigen.

## Einschränkungen

Audit-Logs sind keine Sandbox. Sie unterstützen die Nachvollziehbarkeit, verhindern aber nicht, dass ein verbundenes Modell innerhalb seiner konfigurierten Befugnisse handelt.
