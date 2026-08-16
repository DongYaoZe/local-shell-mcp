<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# 일반 MCP client

`local-shell-mcp`는 ChatGPT뿐 아니라 다른 MCP client에서도 사용할 수 있습니다. client가 HTTP로 연결할지 stdio를 통해 서버를 시작할지를 결정합니다.

## HTTP MCP client

서버가 이미 실행 중이라면 HTTP mode를 사용합니다.

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

로컬 endpoint:

```text
http://127.0.0.1:8765/mcp
```

네트워크 endpoint:

```text
https://your-public-host.example.com/mcp
```

신뢰된 localhost 밖에서 접근 가능한 endpoint에는 OAuth를 사용하십시오.

## Stdio MCP client

client가 서버 프로세스를 직접 시작할 때는 stdio mode를 사용합니다.

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

일반적인 client 설정 형태:

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

client마다 schema가 다릅니다. 이 섹션을 `mcpServers`라고 부르는 client도 있고 다른 이름을 사용하는 client도 있습니다.

## 첫 번째 안전 확인

새로 연결한 client에서는 다음부터 시작하십시오.

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

그 다음 편집, 테스트, Git 규칙을 명확히 지정한 범위가 제한된 작업을 실행하십시오.
