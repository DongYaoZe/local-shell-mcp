<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT 커넥터

이 페이지는 client 연결로서 ChatGPT를 다룹니다. runtime은 선택하지 않습니다. 이 페이지를 사용하기 전에 Docker, VS Code extension, binary 또는 Python install로 서버를 실행하십시오.

`local-shell-mcp`는 ChatGPT Developer Mode와 완전한 MCP client를 위해 설계되었습니다. MCP endpoint는 일반 LSM tool surface를 직접 노출합니다.

## Runtime 사전 조건

먼저 runtime 하나를 선택해 시작합니다:

| Runtime | 페이지 |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

그 다음 ChatGPT에서 접근 가능한 network path로 해당 runtime을 공개합니다. 자세한 내용은 [network connectivity](../clients/connectivity.md).

## 공개 URL

ChatGPT는 HTTPS로 서버에 접근해야 합니다. MCP endpoint는:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL`이 public origin과 일치하는지 확인합니다:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL`에 `/mcp`를 포함하지 마십시오.

## OAuth 설정

공개 환경 권장 설정:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

긴 coding session은 짧은 token lifetime을 넘을 수 있으므로 access token은 기본적으로 만료되지 않습니다. 필요할 때 JWT secret을 rotate하거나 새 state로 재배포해 access를 revoke하십시오.

## 커넥터 추가

1. ChatGPT connector 또는 Developer Mode MCP settings를 엽니다.
2. Custom MCP server를 추가합니다.
3. MCP URL을 입력합니다: `https://your-public-host.example.com/mcp`.
4. OAuth를 완료합니다.
5. Tool surface를 승인합니다.

## Live Workspace MCP App

MCP Apps를 지원하는 ChatGPT client는 `local-shell-mcp`를 대화형 execution workspace로 렌더링할 수 있습니다. 실시간 가시성이나 사람과의 협업이 유용할 때 ChatGPT에 Live Workspace를 한 번 열도록 요청하십시오. 이후 app은 반복적인 `workspace_open` 호출 없이 스스로 재연결합니다.

Live Workspace는 모델 reasoning과 의도적으로 분리되어 있습니다. 관찰 가능한 execution state와 공유 resources를 보여 줍니다:

- **Activity** 는 MCP tool 시작, 완료, 실패 및 사람의 작업을 보여 줍니다.
- **Terminal** 은 기존 persistent shell backend에 연결해 live PTY output을 보여 줍니다.
- **Files** 는 local/remote workspace file을 탐색, preview, edit, create, delete합니다.
- **Diff** 는 staged/unstaged Git changes를 보여 주고 현재 diff를 검토용으로 ChatGPT에 다시 보낼 수 있습니다.
- **Jobs** 는 managed jobs와 persistent sessions를 보여 줍니다.
- **Remotes** 는 workers를 보여 주며 remote support가 활성화되면 invite, rename, revoke 작업을 제공합니다.
- **Audit** 는 최근 structured MCP audit records를 보여 줍니다.

Live Workspace는 항상 collaborative합니다. ChatGPT와 사람이 같은 workspace를 동시에 수정할 수 있습니다. host가 지원하면 floating PiP-style window로 열리고 fullscreen과 windowed 상태를 전환할 수 있습니다. 별도의 observe/takeover state는 없습니다.

File, diff, audit, activity view는 선택한 operational context를 MCP Apps bridge를 통해 다음 model turn으로 보낼 수 있습니다. 이는 명시적으로 공유되는 context이며 UI는 private model reasoning을 노출하거나 재구성하지 않습니다.

### 네트워킹 및 보안

렌더링된 MCP App은 저지연 terminal/event traffic을 위해 sandbox에서 구성된 service origin으로 직접 연결합니다. 따라서 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`은 ChatGPT browser가 접근할 수 있는 HTTPS origin이어야 합니다. MCP endpoint 자체는 `https://your-public-host.example.com/mcp`로 유지됩니다.

Workspace를 열면 무작위의 짧은 수명을 가진 Live Workspace bearer token이 발급됩니다. 이 token은 렌더링된 app용 MCP result metadata에만 포함되며 model-visible structured content에는 들어가지 않고 human/live UI API에서만 허용됩니다. 같은 `live_id`로 자동 재연결할 때 현재 credential을 재사용하여 reconnecting view끼리 서로 무효화하지 않습니다. 또한 현재 logical `session_id`를 함께 전달하므로 메모리의 Live Workspace state가 사라져도 durable Session을 복구할 수 있습니다. 명시적으로 새 `workspace_open`을 호출하면 credential이 교체됩니다. embedded app은 browser cookie나 ambient credential을 사용하지 않습니다.

MCP Apps를 구현하지 않는 client는 UI metadata를 무시할 수 있습니다. 모든 일반 MCP data tools는 그대로 사용 가능하며 동작도 같습니다.

## 첫 prompt

```text
local-shell-mcp를 사용하세요. 먼저 environment_get를 호출한 다음 workspace root를 나열하세요. 아직 파일을 수정하지 마세요.
```

변경 없이 connectivity를 확인합니다.

## 권장 운영 규칙

모델에 명확한 제약을 제공하십시오:

- 명시되지 않은 경우 `/workspace` 안에서 작업합니다.
- commit 전에 tests를 실행합니다.
- push 전에 `secret_scan`을 사용합니다.
- 공유해도 안전한 file에만 `link_create`를 사용합니다.
- 장시간 process에는 persistent shell session을 우선합니다.
- file을 변경한 모든 command를 요약합니다.

## Tool discovery 문제

ChatGPT 인증은 되지만 예상 tools가 보이지 않는 경우:

- endpoint가 `/mcp`로 끝나는지 확인합니다.
- `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`를 확인합니다.
- reverse proxy headers와 request body limits를 확인합니다.
- `docker compose logs --tail=200 local-shell-mcp`를 확인합니다.
- service가 `mcp` 또는 `both` mode인지 확인합니다.

## 안전 참고

공개 deployment에서는 OAuth를 활성화해야 합니다. 인증되지 않은 전체 MCP tools를 public internet에 노출하지 마십시오. 승인한 모든 tool을 connected model의 실질적 권한 일부로 취급하십시오.
