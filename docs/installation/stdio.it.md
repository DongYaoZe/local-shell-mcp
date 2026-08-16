<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Runtime Stdio

La modalità stdio è destinata ai MCP client locali che avviano `local-shell-mcp` come child process e comunicano tramite input/output standard.

Non è un deployment HTTP pubblico. ChatGPT web/app non può usarlo direttamente perché ChatGPT non può avviare un process sulla tua macchina.

## Quando usare stdio

Usa stdio mode quando:

- Il tuo MCP client supporta definizioni server basate su comando.
- Il client e il workspace controllato si trovano sulla stessa macchina.
- Non servono OAuth, HTTPS pubblico, reverse proxy o tunnel.
- Vuoi che il client gestisca il server lifecycle.

Non usare stdio mode quando:

- Il client è ChatGPT web/app.
- Più remote client richiedono lo stesso server.
- Servono download tokenizzati via HTTP.
- Servono route di join dei remote worker servite via HTTP.

## Comando

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Una configurazione generica di MCP client contiene in genere:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Adatta lo schema al tuo client. Alcuni client chiamano questa sezione `servers`, `tools`, `mcpServers` o `contextServers`.

## Differenze rispetto a HTTP mode

| Area | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Nessuno | `/mcp` |
| OAuth | Non necessario | Consigliato per uso pubblico |
| Health endpoint | Nessuno | `/healthz`, `/readyz` |
| Uso pubblico con ChatGPT | No | Sì, dietro HTTPS |
| Server lifecycle | Il client avvia il process | Gestisci tu process/runtime |

La tool surface usa altrimenti la stessa implementazione server-side, soggetta a configuration e supporto del client.

## Note di sicurezza

Stdio mode viene spesso eseguito direttamente sull’host con lo stesso utente del MCP client. Usa un workspace root ristretto ed evita accesso ampio al filesystem. Mantieni full-container mode disabilitato a meno che stdio stesso non venga eseguito in un container o VM usa e getta.
