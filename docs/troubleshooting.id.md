<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Pemecahan masalah

Periksa kesehatan layanan:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Periksa log:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Jika ChatGPT tidak dapat terhubung, pastikan `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` sama persis dengan origin HTTPS publik dan bahwa `/mcp`, metadata OAuth, serta `/healthz` dapat dijangkau melalui tunnel atau reverse proxy.

Jika remote worker tidak muncul, pastikan mode remote aktif, undangan belum kedaluwarsa, dan mesin remote dapat membuat permintaan HTTPS keluar ke server kontrol.
