<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# 문제 해결

서비스 상태를 확인합니다.

```bash
curl -i http://127.0.0.1:8765/healthz
```

로그를 확인합니다.

```bash
docker compose logs --tail=100 local-shell-mcp
```

ChatGPT가 연결할 수 없다면 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`이 실제 공개 HTTPS origin과 정확히 일치하는지, 그리고 `/mcp`, OAuth 메타데이터, `/healthz`가 tunnel 또는 reverse proxy를 통해 접근 가능한지 확인하십시오.

원격 worker가 나타나지 않는다면 remote 모드가 활성화되어 있는지, 초대가 만료되지 않았는지, 원격 머신이 제어 서버로 outbound HTTPS 요청을 보낼 수 있는지 확인하십시오.
