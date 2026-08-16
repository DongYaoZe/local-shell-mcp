<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Rozwiązywanie problemów

Sprawdź stan usługi:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Sprawdź logi:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Jeśli ChatGPT nie może się połączyć, sprawdź, czy `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` dokładnie odpowiada publicznemu HTTPS origin oraz czy `/mcp`, metadane OAuth i `/healthz` są osiągalne przez tunnel lub reverse proxy.

Jeśli zdalne workers nie pojawiają się, sprawdź, czy tryb remote jest włączony, zaproszenie nie wygasło i zdalna maszyna może wysyłać wychodzące żądania HTTPS do serwera sterującego.
