<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# API REST

L’interfaccia principale è MCP su `/mcp`. È disponibile anche una superficie REST per health check, file link e operazioni di servizio selezionate.

## Stato

```http
GET /healthz
```

Restituisce lo stato di salute del server e informazioni di base sullo stato.

## MCP

```http
POST /mcp
```

Endpoint MCP Streamable HTTP usato da ChatGPT e dagli altri MCP client.

## Chiamate agli strumenti via REST

Le chiamate REST agli strumenti usano envelopes coerenti per successo ed errore. Gli errori di validazione restituiscono payload strutturati `ok: false` invece di eccezioni grezze del framework.

## Agent Skills

Il registro fisso delle Skills è disponibile anche via REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Le modifiche alle directory delle Skill sono visibili alla chiamata successiva e non modificano l’elenco degli strumenti MCP.

## Link ai file

I download tokenizzati sono serviti dall’app HTTP integrata. I link sono bearer URL con TTL, limite massimo opzionale di download e supporto per la revoca.

## Autenticazione

Le distribuzioni pubbliche dovrebbero usare OAuth. Il bypass di localhost può essere abilitato per lo sviluppo, ma l’accesso pubblico non autenticato non è sicuro.
