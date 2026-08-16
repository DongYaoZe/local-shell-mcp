<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Solução de problemas

Verifique a integridade do serviço:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Verifique os logs:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Se o ChatGPT não conseguir se conectar, confirme que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` corresponde exatamente ao origin HTTPS público e que `/mcp`, os metadados do OAuth e `/healthz` podem ser alcançados pelo tunnel ou proxy reverso.

Se os workers remotos não aparecerem, confirme que o modo remote está habilitado, que o convite não expirou e que a máquina remota consegue fazer requisições HTTPS de saída para o servidor de controle.
