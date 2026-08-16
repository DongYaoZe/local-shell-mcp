<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# VS Code extension runtime

VS Code extension은 동일한 `local-shell-mcp` server를 위한 launcher 및 convenience UI입니다. 현재 editor workspace용 server process를 시작하므로 runtime 선택입니다.

ChatGPT connector 자체는 아닙니다. ChatGPT web/app에서 사용할 때 ChatGPT는 여전히 public HTTPS `/mcp` endpoint에 연결합니다.

## Extension 기능

Extension은:

- 현재 VS Code workspace용 `local-shell-mcp`를 시작합니다.
- Server를 stop/restart합니다.
- VS Code output channel에 server output을 표시합니다.
- `/healthz`를 확인합니다.
- MCP URL을 copy합니다.
- Workspace와 endpoint가 포함된 ChatGPT setup prompt를 copy합니다.

Extension은 server binary를 bundle하지 않습니다. `local-shell-mcp`를 별도로 install하고 `PATH`에 없다면 extension에 executable path를 지정하십시오.

## 사용 시점

다음 경우 이 runtime을 사용합니다:

- 보통 VS Code folder에서 작업을 시작합니다.
- Terminal command를 직접 실행하는 대신 button/command-palette flow가 필요합니다.
- Project dependencies가 host에 이미 설치되어 있습니다.
- Trusted repository 또는 좁은 workspace에서 작업합니다.
- 그 workspace만 model에 공개하는 데 동의합니다.

다음 경우 Docker를 사용합니다:

- Repository가 untrusted입니다.
- Task가 arbitrary packages를 install합니다.
- 폭넓은 preinstalled toolchain이 필요합니다.
- Container 재생성으로 쉽게 reset하고 싶습니다.
- Host account보다 깔끔한 boundary가 필요합니다.

## Executable 설치

Server install method 하나를 선택합니다:

```bash
pipx install local-shell-mcp
```

또는 OS용 release binary를 내려받아 `PATH`에 둡니다.

그 다음 VSIX release asset을 설치합니다:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

또는 command palette의 **Extensions: Install from VSIX...**를 사용합니다.

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | MCP에 공개할 workspace | 첫 VS Code folder는 empty 또는 explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Prompt/URL에 copy되는 public HTTPS origin | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | OAuth authorization용 PIN | Public use에는 strong random value |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Direct host usage에서는 `false` 유지 |
| `local-shell-mcp.extraEnv` | Server process의 extra environment | Project-specific safe values만 |

## 기본 flow

1. VS Code에서 project folder를 엽니다.
2. **local-shell-mcp: Start Server**를 실행합니다.
3. 가능하면 **Show Server Status** 또는 **Check Health**를 실행합니다.
4. Local MCP client에는 **Copy MCP URL**, ChatGPT에는 **Copy ChatGPT Setup Prompt**를 실행합니다.
5. Endpoint를 client에 추가합니다.

Local endpoint는 보통:

```text
http://127.0.0.1:8765/mcp
```

Local client에는 유용하지만 ChatGPT web/app에서는 접근할 수 없습니다.

## ChatGPT와 사용

VS Code-launched server를 ChatGPT에서 쓰려면 local port 앞에 HTTPS tunnel 또는 reverse proxy를 추가합니다.

예:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

설정:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

ChatGPT용으로 copy되는 URL은 `/mcp`로 끝나야 합니다:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Extension은 보통 host user 권한으로 commands를 실행합니다. 이는 disposable Docker container와 실질적으로 다릅니다.

권장 규칙:

- Model에 control시킬 repository만 엽니다.
- `allowFullContainer`를 비활성화 상태로 둡니다.
- Workspace root를 home directory로 지정하지 않습니다.
- 무관한 secrets를 workspace에 두지 않습니다.
- Commit/push 전에 `secret_scan`을 사용합니다.
- Unfamiliar repository 또는 package-install-heavy task에는 Docker를 선호합니다.

## 일반 prompt

Setup prompt를 copy한 뒤 read-only task로 시작합니다:

```text
local-shell-mcp를 사용하세요. 먼저 environment_get와 workspace에 대한 file_tree를 호출하세요. 아직 파일을 수정하지 마세요.
```

그 다음 bounded edit으로 이동합니다:

```text
이 workspace의 failing test를 수정하세요. 먼저 relevant files를 읽고 최소 patch를 만든 뒤 targeted test를 실행하고 git diff를 보여 주세요. 승인할 때까지 commit하지 마세요.
```

## 문제 해결

| 증상 | 확인 |
|---|---|
| Extension이 server를 시작할 수 없음 | `local-shell-mcp.executablePath`가 존재하고 terminal에서 `--help`가 동작하는지 확인 |
| ChatGPT가 접근할 수 없음 | Local `127.0.0.1` URL은 public이 아니므로 tunnel/proxy와 `publicBaseUrl` 설정 |
| Tools가 잘못된 folder 노출 | `local-shell-mcp.workspaceRoot`를 명시적으로 설정 |
| Restart 후 auth 실패 | `extraEnv` 또는 runtime configuration으로 stable OAuth admin PIN과 JWT secret 설정 |
| Commands에 dependencies 없음 | Host에 dependencies를 설치하거나 Docker runtime으로 전환 |
