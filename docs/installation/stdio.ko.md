<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Stdio mode는 `local-shell-mcp`를 child process로 시작하고 표준 입력/출력으로 통신하는 로컬 MCP client용입니다.

공개 HTTP deployment가 아닙니다. ChatGPT는 사용자 머신에서 process를 생성할 수 없으므로 ChatGPT web/app에서 직접 사용할 수 없습니다.

## stdio 사용 시점

다음 경우 stdio mode를 사용하십시오.

- MCP client가 command-based server definition을 지원합니다.
- client와 제어 대상 workspace가 같은 머신에 있습니다.
- OAuth, 공개 HTTPS, reverse proxy 또는 tunnel이 필요하지 않습니다.
- client가 server lifecycle을 관리하게 하고 싶습니다.

다음 경우 stdio mode를 사용하지 마십시오.

- client가 ChatGPT web/app입니다.
- 여러 remote client가 같은 server를 필요로 합니다.
- HTTP를 통한 tokenized file download가 필요합니다.
- HTTP로 제공되는 remote-worker join route가 필요합니다.

## 명령

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

일반적인 MCP client 설정은 보통 다음 형태를 포함합니다.

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

client에 맞게 schema를 조정하십시오. 어떤 client는 이를 `servers`, `tools`, `mcpServers`, `contextServers`라고 부릅니다.

## HTTP mode와의 동작 차이

| 영역 | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | 없음 | `/mcp` |
| OAuth | 필요 없음 | 공개 사용 시 권장 |
| Health endpoint | 없음 | `/healthz`, `/readyz` |
| 공개 ChatGPT 사용 | 불가 | HTTPS 뒤에서 가능 |
| Server lifecycle | client가 process 시작 | 사용자가 process/runtime 관리 |

그 외 tool surface는 configuration과 client support 범위 내에서 동일한 server-side implementation을 사용합니다.

## 안전 참고

Stdio mode는 흔히 MCP client와 같은 user로 host에서 직접 실행됩니다. workspace root를 좁게 유지하고 광범위한 filesystem access를 피하십시오. stdio 자체가 폐기 가능한 container 또는 VM 안에서 실행되는 경우가 아니라면 full-container mode를 비활성화하십시오.
