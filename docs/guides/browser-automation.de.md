<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Browser-Automatisierung

Browser-Tools verwenden Playwright, um Seiten zu untersuchen, Nachweise zu erfassen und reproduzierbare Browser-Workflows auszuführen. Die öffentliche Tool-Oberfläche ist bewusst klein gehalten.

## Tools

| Tool | Zweck |
|---|---|
| `browser_session` | Persistente Browser-Sitzungen starten, auflisten, schließen oder bereinigen; optional ein Profile oder Storage State wiederverwenden. |
| `browser_snapshot` | Begrenzten Seitentext, Page-/Network-Fehler und interaktive Elemente mit kurzen Refs wie `e1` lesen; optional einen Screenshot aufnehmen. |
| `browser_act` | Strukturierte Navigation-, Click-, Fill-, Select-, Key-, Wait- und Mehrseiten-Aktionen über Snapshot-Refs oder CSS-Selektoren ausführen. |
| `browser_run_script` | Ein vollständiges Python-Playwright-Skript ausführen, wenn der Satz von High-Level-Aktionen nicht ausreicht. |

Alle Browser-Tools akzeptieren optional `machine`. Browser-Abhängigkeiten müssen auf dem ausgewählten Controller oder Worker bereits installiert sein; installiert wird mit normalen Shell-Befehlen wie `python -m playwright install chromium`.

## Übliche Abläufe

Rufen Sie für interaktive Arbeit zuerst `browser_session(action="start", url=...)` und dann `browser_snapshot` auf. Der Snapshot liefert kurze Referenzen wie `e1` und `e2`; übergeben Sie diese direkt an `browser_act`, etwa `{"action": "click", "target": "e1"}` oder `{"action": "fill", "target": "e2", "value": "..."}`. Erstellen Sie nach Navigation einen neuen Snapshot, da Element-Refs Zustandsreferenzen der Seite und keine permanenten Selektoren sind.

Für normale Inspektionen und Screenshots bevorzugen Sie `browser_session` plus `browser_snapshot`; der Snapshot kann begrenzten sichtbaren Text zurückgeben und einen Screenshot speichern. Verwenden Sie `browser_run_script` für JavaScript-Auswertung, benutzerdefinierte Capture-/PDF-Logik oder Interaktionen, die `browser_act` nicht abbildet.

Halten Sie Skripte begrenzt, setzen Sie explizite Timeouts, speichern Sie Artefakte unter dem Workspace und vermeiden Sie die Eingabe von Credentials, sofern die Umgebung nicht ausschließlich für die Aufgabe vorgesehen ist.
