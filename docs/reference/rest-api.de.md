<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST-API

Die primäre Schnittstelle ist MCP unter `/mcp`. Eine REST-Oberfläche ist außerdem für Health Checks, File Links und ausgewählte Service-Operationen verfügbar.

## Health

```http
GET /healthz
```

Gibt den Gesundheitszustand und grundlegende Statusinformationen des Servers zurück.

## MCP

```http
POST /mcp
```

Streamable-HTTP-MCP-Endpoint für ChatGPT und andere MCP client.

## Tool-Aufrufe über REST

REST-Tool-Aufrufe verwenden konsistente Erfolgs-/Fehler-Envelopes. Validierungsfehler liefern strukturierte `ok: false`-Payloads statt unverarbeiteter Framework-Ausnahmen.

## Agent Skills

Die feste Skills-Registry ist auch über REST verfügbar:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Änderungen an Skill-Verzeichnissen sind beim nächsten Aufruf sichtbar und verändern die MCP-Tool-Liste nicht.

## Dateilinks

Tokenisierte Dateidownloads werden von der integrierten HTTP-App bereitgestellt. Die Links sind Bearer-URLs mit TTL, optionalem maximalem Download-Limit und Widerrufsmöglichkeit.

## Authentifizierung

Öffentliche Bereitstellungen sollten OAuth verwenden. Für die Entwicklung kann ein localhost-Bypass aktiviert werden; unauthentifizierter öffentlicher Zugriff ist jedoch unsicher.
