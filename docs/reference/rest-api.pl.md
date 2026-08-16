<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

Podstawowym interfejsem jest MCP pod `/mcp`. Dostępna jest także powierzchnia REST dla health checks, file links i wybranych operacji usługowych.

## Stan

```http
GET /healthz
```

Zwraca stan zdrowia serwera i podstawowe informacje o stanie.

## MCP

```http
POST /mcp
```

Streamable HTTP MCP endpoint używany przez ChatGPT i inne MCP client.

## Wywołania narzędzi przez REST

Wywołania narzędzi REST używają spójnych envelopes sukcesu/błędu. Błędy walidacji zwracają ustrukturyzowane payloads `ok: false` zamiast surowych wyjątków frameworka.

## Agent Skills

Stały rejestr Skills jest również dostępny przez REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Zmiany w katalogach Skill są widoczne przy następnym wywołaniu i nie zmieniają listy narzędzi MCP.

## Linki do plików

Tokenizowane pobieranie plików obsługuje wbudowana aplikacja HTTP. Linki są bearer URL z TTL, opcjonalnym maksymalnym limitem pobrań i obsługą unieważnienia.

## Uwierzytelnianie

Publiczne wdrożenia powinny używać OAuth. Na potrzeby rozwoju można włączyć localhost bypass, ale nieuwierzytelniony dostęp publiczny jest niebezpieczny.
