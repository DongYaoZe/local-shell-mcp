<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Dépannage

Vérifiez l’état du service :

```bash
curl -i http://127.0.0.1:8765/healthz
```

Vérifiez les journaux :

```bash
docker compose logs --tail=100 local-shell-mcp
```

Si ChatGPT ne peut pas se connecter, vérifiez que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` correspond exactement à l’origin HTTPS public et que `/mcp`, les métadonnées OAuth et `/healthz` sont accessibles via le tunnel ou le proxy inverse.

Si les workers distants n’apparaissent pas, vérifiez que le mode remote est activé, que l’invitation n’a pas expiré et que la machine distante peut émettre des requêtes HTTPS sortantes vers le serveur de contrôle.
