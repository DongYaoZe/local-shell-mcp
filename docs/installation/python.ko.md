<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Python, pipx 및 source runtimes

Python runtime은 개발, 디버깅 또는 Docker보다 Python package management가 쉬운 환경에 적합합니다. Docker 및 binary runtime과 동일한 server를 실행합니다.

이 페이지는 세 가지 관련 경우를 다룹니다.

- `pipx install local-shell-mcp`: user-level executable install.
- `pip install local-shell-mcp`: 기존 virtual environment에 install.
- Editable source checkout: project 자체 개발 또는 디버깅.

## pipx install

일반 사용자에게 `pipx`는 가장 깔끔한 Python-based install입니다. command별 virtual environment를 제공하면서 executable을 `PATH`에 노출합니다.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

로컬 HTTP MCP server를 시작합니다.

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Health 확인:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Virtual environment install

Python environment를 직접 관리하는 경우 사용합니다.

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

process는 host에 설치된 tool을 사용합니다. Python package가 compiler, Git, browser system dependency 또는 project dependency를 대신 설치하지 않습니다.

## Editable source checkout

project 개발에는 다음을 사용합니다.

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

검사 실행:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Browser setup

Python package는 Playwright에 의존하지만 browser binary는 host에 별도 설치가 필요할 수 있습니다.

```bash
python -m playwright install chromium
```

일부 Linux host에는 추가 browser dependency도 필요합니다. Docker는 Playwright base image에서 시작하므로 대부분의 작업을 피할 수 있습니다.

## Public HTTP MCP use

ChatGPT 또는 다른 public HTTP MCP client에서 사용할 경우 다른 HTTP runtime과 같은 public-origin 및 OAuth 설정을 구성한 다음 local port를 reverse proxy 또는 tunnel로 공개합니다.

공개 MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

## Development modes

| Mode | Command | 용도 |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | HTTPS 뒤의 ChatGPT를 포함한 HTTP 기반 전체 MCP client |
| REST-style HTTP | `local-shell-mcp --mode http` | 진단 또는 호환 endpoint; 주 ChatGPT 경로가 아님 |
| stdio | `local-shell-mcp --mode stdio` | process를 시작하는 로컬 MCP client |

`mode=both`는 예약되어 있으며 현재 단일 process mode로 사용하면 안 됩니다.

## Host-runtime safety

Python install은 VM/container에 넣지 않는 한 host user 권한으로 실행됩니다. workspace를 좁게 유지하고 full-container mode를 비활성화하며 workspace를 home directory로 지정하지 마십시오.

신뢰할 수 없는 repository, package-manager 사용이 많은 task 또는 host integration보다 resetability가 중요한 workflow에는 Docker Compose를 사용하십시오.
