<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Solución de problemas

Compruebe el estado del servicio:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Compruebe los registros:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Si ChatGPT no puede conectarse, verifique que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` coincida exactamente con el origin HTTPS público y que `/mcp`, los metadatos de OAuth y `/healthz` sean accesibles a través del tunnel o del proxy inverso.

Si los workers remotos no aparecen, confirme que el modo remote esté habilitado, que la invitación no haya caducado y que la máquina remota pueda realizar solicitudes HTTPS salientes al servidor de control.
