<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">ChatGPT 호환 MCP control plane</span>

# local-shell-mcp

Chat을 떠나지 않고 AI assistant에 제어된 shell, 실제 workspace, Git, browser automation, file sharing, remote-worker access를 제공합니다.

<div class="hero-actions" markdown>
[시작하기](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Runtime 선택](guides/deployment.md){ .hero-action .hero-action--secondary }
[Tools reference](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### 실제 coding environment
하나의 MCP endpoint에서 tests 실행, repository 검사, file patch, Git 조작, audit trail 유지를 수행합니다.
</div>

<div class="feature-card" markdown>
### Runtime 및 client 레이어
Docker, VS Code extension, binary, Python, stdio 같은 runtime을 고른 다음 ChatGPT 또는 다른 MCP client를 별도로 연결합니다.
</div>

<div class="feature-card" markdown>
### Remote machine control
SSH port를 열지 않고 outbound worker connection으로 NAT, firewall 또는 HPC machine을 연결합니다.
</div>
</div>

## 제공 기능

`local-shell-mcp`는 제어된 local/container workspace를 ChatGPT와 다른 MCP client에 노출합니다. Shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, optional Goal Plan이 있는 durable logical Session, tokenized file link, remote-worker tool을 OAuth 지원 ChatGPT-compatible MCP server로 제공합니다.

AI가 repository를 검사하고 tests를 실행하고 files를 편집하고 Git을 조작하고 browser evidence를 수집하고 downloadable artifacts를 만들거나 control server로 outbound 연결만 가능한 remote machine을 제어해야 할 때 사용합니다.

## 아키텍처

```text
Runtime layer: Docker / VS Code extension / binary / Python / stdio
Exposure layer: localhost / HTTPS proxy / tunnel / stdio pipe
Client layer: ChatGPT / generic MCP client / editor helper
Controlled workspace: /workspace or configured workspace root
Optional remote workers: outbound machine connections
```

의도된 isolation boundary는 service를 실행하는 container 또는 VM입니다.

## 시나리오별 시작

| 시나리오 | 시작 페이지 | 이유 |
|---|---|---|
| 첫 public ChatGPT deployment | [Quickstart](getting-started/quickstart.md) | OAuth와 `/mcp` 설정을 포함한 Docker Compose 경로 |
| runtime layer 선택 | [Runtime choices](guides/deployment.md) | Docker, VS Code, binary, Python, stdio를 별도 runtime option으로 설명 |
| ChatGPT를 client로 추가 | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, 첫 안전 prompt, tool discovery |
| LSM을 DeepSeek Harness에 추가 | [DeepSeek Harness plugin](clients/deepseek-harness.md) | 이 repository를 DSH bundle로 설치하면서 전체 LSM tool 및 remote-worker surface 유지 |
| VS Code에서 실행 | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime 및 host safety 참고 |
| toolset 운영 방법 학습 | [Usage patterns](guides/usage-patterns.md) | Prompt template과 tool 선택 안내 |
| 모든 tool 이해 | [Tools reference](reference/tools.md) | 각 tool의 purpose, inputs, returns, combinations, notes |
| HPC, NPU/GPU 또는 server node 연결 | [Remote workers](guides/remote-workers.md) | Outbound worker join flow 및 remote tool usage |
| 생성 file 공유 | [File links](guides/file-links.md) | TTL과 revoke를 지원하는 tokenized download URL |
| deployment hardening | [Security](security.md) | Isolation, OAuth, workspace scope, audit logs |

## 주요 tool family

| Family | 예 | 용도 |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Build, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection 및 precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Review 가능한 source-control workflow |
| Sessions 및 Goal | `session_manage`, `plan_manage` | durable task handoff, progress report, optional Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI check, screenshot, rendered docs, page text |
| File links | `link_create`, `link_revoke` | Chat에서 generated artifacts 다운로드 |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | NAT, firewall 또는 cluster login flow 뒤의 machine |

## 대표 workflow

### ChatGPT로 coding

1. 전용 workspace에서 Docker Compose, VS Code extension, binary, Python 같은 runtime을 시작합니다.
2. ChatGPT에 network access가 필요하면 HTTP runtime을 공개합니다.
3. Public `/mcp` endpoint를 ChatGPT에 추가합니다.
4. 먼저 repository 검사와 read-only checks를 요청합니다.
5. 승인되면 file patch, tests, diff review, commit, push를 수행하게 합니다.
6. File link 또는 remote system이 관련된 task에서는 audit log를 확인합니다.

### Remote HPC 또는 accelerator host

1. 일회성 remote worker invite를 만듭니다.
2. 생성 command를 remote host에 붙여넣습니다.
3. 일반 tools에 `machine`을 사용하고 Git은 `run_shell`, path transfer는 `remote_transfer`를 사용합니다.
4. Task 후 worker를 revoke합니다.

### Artifact generation

1. AI가 `/workspace` 아래에 file을 생성하도록 합니다.
2. TTL/download limit가 있는 tokenized file link를 만듭니다.
3. Link를 chat에 공유합니다.
4. 완료되면 revoke합니다.

## 언어

이 site는 native MkDocs i18n plugin으로 build됩니다. Header의 language selector로 English와 translated pages를 전환합니다. 번역이 없는 page는 English로 fallback됩니다.
