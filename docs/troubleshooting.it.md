<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Risoluzione dei problemi

Controlla lo stato del servizio:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Controlla i log:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Se ChatGPT non riesce a connettersi, verifica che `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` corrisponda esattamente all’origin HTTPS pubblico e che `/mcp`, i metadati OAuth e `/healthz` siano raggiungibili tramite tunnel o reverse proxy.

Se i worker remoti non compaiono, verifica che la modalità remote sia abilitata, che l’invito non sia scaduto e che la macchina remota possa effettuare richieste HTTPS in uscita verso il server di controllo.
