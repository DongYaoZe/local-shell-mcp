<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Runtime 선택과 deployment 모델

`local-shell-mcp`에는 서로 독립적인 두 가지 결정이 있습니다:

1. **Runtime**: server process를 어떻게 실행하고 어떤 workspace를 제어할지.
2. **Client connection**: ChatGPT 또는 다른 MCP client가 그 server에 어떻게 접근할지.

ChatGPT를 deployment 방법으로 취급하지 마십시오. ChatGPT는 client입니다. Docker, VS Code extension, release binary, Python install, stdio mode가 runtime 선택지입니다.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

일반적인 public setup:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

local MCP client setup은 더 단순할 수 있습니다:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Runtime 선택 매트릭스

| Runtime | 적합한 용도 | Isolation boundary | Toolchain source | Public ChatGPT access | 페이지 |
|---|---|---|---|---|---|
| Docker Compose | 대부분의 coding-agent workload와 재현 가능한 workspace | Container | Project image에 폭넓은 기본 toolchain 포함 | HTTPS proxy 또는 tunnel 추가 | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Cloudflare Tunnel을 포함한 단일 stack public deployment | Container | Project image | Compose `tunnel` profile에 내장 | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | editor workspace에서 server 시작/중지 | 대개 host process | host tools와 설정된 executable | ChatGPT용 외부 HTTPS tunnel/proxy 추가 | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Docker를 사용할 수 없는 host/VM | Host or VM | host tools와 설정된 executable | HTTPS proxy 또는 tunnel 추가 | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native 사용, debug, development | Host virtualenv or VM | Python package와 host tools | HTTPS proxy 또는 tunnel 추가 | [Python install](../installation/python.md) |
| Stdio mode | tool process를 직접 spawn하는 local MCP client | Client process boundary | host tools와 설정된 executable | ChatGPT web/app에서는 사용 불가 | [Stdio mode](../installation/stdio.md) |

## Client 연결 매트릭스

| Client path | Public HTTPS 필요 | `/mcp` 사용 | OAuth 필요 | 일반 runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | 예 | 예 | public 사용 시 예 | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | 아니요 | 아니요 | 아니요 | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | localhost는 보통 아니요, 네트워크에서는 예 | 예 | localhost 밖에서는 권장 | Any HTTP runtime |
| VS Code extension helper flow | ChatGPT 연결 시에만 | ChatGPT URL copy 시 예 | ChatGPT에서는 권장 | VS Code-launched runtime |

참조: [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## 각 runtime이 제어하는 것

모든 runtime은 동일한 server code를 실행하고, 활성화된 경우 동일한 MCP tool family를 제공합니다:

- Shell 및 persistent shell sessions.
- Filesystem, search, patch tools.
- Git operations.
- Playwright 기반 browser automation.
- Audit log 및 task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle 및 machine-routed tools.

차이는 추상 API가 아니라 그 뒤의 **operating environment**입니다.

| 질문 | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Command 실행 위치? | container 내부 | 대개 host workspace | host 또는 VM process environment |
| Default workspace? | Mounted `/workspace` | 현재 VS Code folder 또는 설정 path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser preinstall? | 폭넓게 포함 | host에 설치된 것만 | host에 설치된 것만 |
| Reset이 쉬운가? | container와 workspace volume 재생성 | workspace에 따라 다름 | host/VM에 따라 다름 |
| 임의 package install에 적합? | disposable이면 예 | host에서는 위험 증가 | VM이 아니면 위험 증가 |

## 권장 선택

특별한 이유가 없다면 **Docker Compose**부터 사용하십시오. 가장 명확한 safety boundary와 가장 완전한 기본 toolchain을 제공합니다.

workflow가 editor에서 시작하고 local launcher가 필요하면 **VS Code extension**을 사용하십시오. 이것도 runtime입니다. 그 자체로 ChatGPT에서 접근 가능해지는 것은 아니므로 ChatGPT web/app에서는 tunnel 또는 reverse proxy를 추가해야 합니다.

Docker를 사용할 수 없지만 VM/container host/dedicated user account가 boundary를 제공한다면 **standalone binary**를 사용하십시오.

`local-shell-mcp` 자체 development/debug 또는 Python-based environment 관리가 더 쉽다면 **`pipx` 또는 source install**을 사용하십시오.

server process를 spawn할 수 있는 local MCP client에만 **stdio mode**를 사용하십시오. public deployment가 아니며 ChatGPT web/app에서 직접 사용할 수 없습니다.

## Public endpoint 규칙

ChatGPT 같은 HTTP MCP client의 MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL`은 origin만 지정합니다:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL`에 `/mcp`를 붙이지 마십시오.

## Runtime 페이지

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Client 페이지

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
