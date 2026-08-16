<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Python、pipx、source runtimes

Python runtime は、開発、デバッグ、または Docker より Python package management の方が扱いやすい環境に適しています。Docker runtime や binary runtime と同じ server を実行します。

このページは次の 3 つの関連ケースを扱います。

- `pipx install local-shell-mcp`: user-level executable install。
- `pip install local-shell-mcp`: 既存 virtual environment への install。
- Editable source checkout: project 自体の開発やデバッグ。

## pipx install

通常のユーザーには `pipx` が最も扱いやすい Python-based install です。command 専用の virtual environment を作りつつ、executable を `PATH` に公開します。

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

ローカル HTTP MCP server を起動します。

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Health を確認します。

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Virtual environment install

Python environment を自分で管理している場合はこちらを使います。

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

process は host にインストールされた tool を使用します。Python package が compiler、Git、browser system dependency、project dependency を代わりにインストールすることはありません。

## Editable source checkout

project 開発では次を使用します。

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

チェックを実行します。

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Browser setup

Python package は Playwright に依存していますが、browser binary は host 側で別途インストールが必要な場合があります。

```bash
python -m playwright install chromium
```

Linux host によっては追加の browser dependency も必要です。Docker は Playwright base image を使用するため、この作業の大部分を避けられます。

## Public HTTP MCP use

ChatGPT または別の public HTTP MCP client で使う場合は、他の HTTP runtime と同じ public-origin/OAuth 設定を行い、local port を reverse proxy または tunnel 経由で公開します。

公開 MCP endpoint：

```text
https://your-public-host.example.com/mcp
```

## Development modes

| Mode | Command | 用途 |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | HTTPS 背後の ChatGPT を含む、HTTP 経由の完全な MCP client |
| REST-style HTTP | `local-shell-mcp --mode http` | 診断または互換 endpoint。ChatGPT の主経路ではありません |
| stdio | `local-shell-mcp --mode stdio` | process を起動するローカル MCP client |

`mode=both` は予約済みで、現在は単一 process mode として使用すべきではありません。

## Host-runtime safety

Python install は VM/container に入れない限り host user の権限で実行されます。workspace を狭くし、full-container mode は無効にしたまま、workspace を home directory に向けないでください。

信頼できない repository、package-manager を多用する task、または host integration より resetability が重要な workflow では Docker Compose を使用してください。
