<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Sorun giderme

Hizmet durumunu kontrol edin:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Günlükleri kontrol edin:

```bash
docker compose logs --tail=100 local-shell-mcp
```

ChatGPT bağlanamıyorsa `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` değerinin genel HTTPS origin ile tam olarak eşleştiğini ve `/mcp`, OAuth meta verileri ile `/healthz` yollarına tunnel veya reverse proxy üzerinden erişilebildiğini doğrulayın.

Remote worker’lar görünmüyorsa remote modunun etkin olduğunu, davetin süresinin dolmadığını ve uzak makinenin kontrol sunucusuna giden HTTPS istekleri gönderebildiğini doğrulayın.
