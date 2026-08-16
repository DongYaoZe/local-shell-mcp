<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# 疑難排解

檢查服務健康狀態：

```bash
curl -i http://127.0.0.1:8765/healthz
```

檢查日誌：

```bash
docker compose logs --tail=100 local-shell-mcp
```

如果 ChatGPT 無法連線，請確認 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 與實際公開的 HTTPS origin 完全一致，並確認 `/mcp`、OAuth 中繼資料與 `/healthz` 都能透過 tunnel 或反向代理存取。

如果遠端 worker 沒有出現，請確認已啟用 remote 模式、邀請尚未過期，而且遠端機器可以向控制伺服器發出對外 HTTPS 請求。
