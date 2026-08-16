<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Fehlerbehebung

Prüfen Sie den Dienststatus:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Prüfen Sie die Logs:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Wenn ChatGPT keine Verbindung herstellen kann, prüfen Sie, ob `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` exakt dem öffentlichen HTTPS-Origin entspricht und ob `/mcp`, die OAuth-Metadaten und `/healthz` über Tunnel oder Reverse Proxy erreichbar sind.

Wenn Remote-Worker nicht erscheinen, prüfen Sie, ob der Remote-Modus aktiviert ist, die Einladung noch gültig ist und die entfernte Maschine ausgehende HTTPS-Anfragen an den Kontrollserver senden kann.
