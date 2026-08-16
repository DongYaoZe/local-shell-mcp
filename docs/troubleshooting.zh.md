<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# 故障排查

检查服务健康状态：

```bash
curl -i http://127.0.0.1:8765/healthz
```

检查日志：

```bash
docker compose logs --tail=100 local-shell-mcp
```

如果 ChatGPT 无法连接，请确认 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 与实际公开的 HTTPS origin 完全一致，并确认 `/mcp`、OAuth 元数据以及 `/healthz` 都能通过 tunnel 或反向代理访问。

如果远程 worker 没有出现，请确认已启用 remote 模式、邀请尚未过期，并且远程机器能够向控制服务器发起出站 HTTPS 请求。
