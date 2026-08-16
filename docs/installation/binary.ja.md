<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Standalone binary runtime

Release binary を使うと、Docker や Python environment なしで `local-shell-mcp` を実行できます。Docker を利用できない場合、または dedicated VM、container host、lab server、restricted user account がすでに安全境界を提供している場合に、この runtime を使用します。

これは runtime の選択です。ChatGPT access は HTTPS `/mcp` endpoint を通じて別途設定します。

## Release artifacts

GitHub Releases では一般的な platform 向けに self-contained executable を build します。

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

各 archive には executable、README、license、短い quickstart file が含まれます。

## Install

1. GitHub Releases から platform に合う archive を download します。
2. 展開します。
3. executable を `PATH` に置くか、absolute path を記録します。
4. `local-shell-mcp --help` を実行し、binary が起動することを確認します。

Linux/macOS では通常 executable bit が必要です。

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

Windows では PowerShell から `local-shell-mcp.exe` を実行するか、含まれる directory を `PATH` に設定します。

## Minimal local run

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

別の terminal で：

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Public HTTP MCP run

ChatGPT または public HTTP MCP client で使う場合は、次の設定カテゴリを指定します。

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | tool が制御する directory |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | local bind address と port |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | `/mcp` を含まない public HTTPS origin |
| `LOCAL_SHELL_MCP_AUTH_MODE` | public deployment では `oauth` を使用 |
| OAuth PIN and JWT secret settings | public OAuth authorization に必要 |

local HTTP port を reverse proxy または tunnel 経由で公開します。public endpoint：

```text
https://your-public-host.example.com/mcp
```

## YAML config

secret ではない runtime default は YAML config に保存できます。

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

実行：

```bash
local-shell-mcp --config /path/to/config.yaml
```

`LOCAL_SHELL_MCP_` prefix の environment variable は YAML value を上書きします。

## Host toolchain responsibility

binary が package するのは Python application であり、すべての developer tool ではありません。MCP tool は host で利用可能な program を呼び出します。

必要なものを host にインストールしてください。

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; Linux release には static tmux helper が含まれます |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

この host toolchain を自分で管理したくない場合は Docker Compose を使用してください。

## Long-running service

persistent public deployment では、OS の process supervisor の下で binary を実行します。次を守ってください。

- dedicated low-privilege OS account を使う。
- dedicated workspace directory を使う。
- sensitive value を world-readable file の外に保存する。
- failure 時に自動 restart する。
- restart ごとに `/healthz` を確認する。
- troubleshooting 用に log を保持する。

## Updates

1. platform 用の新しい release archive を download します。
2. 必要なら checksum を verify します。
3. executable を置き換えます。
4. process manager を restart します。
5. `/healthz` を確認します。
6. 作業を続ける前に client から `environment_get` を実行します。

## Safety notes

binary は OS user の権限で実行されます。public deployment では dedicated low-privilege user、dedicated workspace、可能なら VM/container boundary を使用してください。

personal host 上で直接実行する binary に `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` を設定しないでください。この設定は disposable container/VM 向けです。
