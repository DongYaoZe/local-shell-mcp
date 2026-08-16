<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Runtime の選択とデプロイモデル

`local-shell-mcp` では 2 つの独立した判断があります：

1. **Runtime**: server process をどのように実行し、どの workspace を制御するか。
2. **Client connection**: ChatGPT または別の MCP client がその server にどう到達するか。

ChatGPT を deployment method として扱わないでください。ChatGPT は client です。Docker、VS Code extension、release binary、Python install、stdio mode が runtime の選択肢です。

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

一般的な public setup：

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

local MCP client の setup はさらに単純です：

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Runtime 選択マトリクス

| Runtime | 最適な用途 | Isolation boundary | Toolchain source | Public ChatGPT access | ページ |
|---|---|---|---|---|---|
| Docker Compose | 一般的な coding-agent workload と再現可能な workspace | Container | Project image に広い標準 toolchain を含む | HTTPS proxy または tunnel を追加 | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Cloudflare Tunnel を含む 1-stack public deployment | Container | Project image | Compose `tunnel` profile に内蔵 | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | editor workspace から server を start/stop | 通常 host process | host tools と設定済み executable | ChatGPT 用に外部 HTTPS tunnel/proxy を追加 | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Docker が使えない host/VM | Host or VM | host tools と設定済み executable | HTTPS proxy または tunnel を追加 | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native 利用、debug、development | Host virtualenv or VM | Python package と host tools | HTTPS proxy または tunnel を追加 | [Python install](../installation/python.md) |
| Stdio mode | tool process を直接 spawn する local MCP client | Client process boundary | host tools と設定済み executable | ChatGPT web/app では使用不可 | [Stdio mode](../installation/stdio.md) |

## Client 接続マトリクス

| Client path | Public HTTPS 必須 | `/mcp` 使用 | OAuth 必須 | 典型 runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | はい | はい | public 利用では必須 | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | いいえ | いいえ | いいえ | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | localhost では通常不要、network 越しでは必要 | はい | localhost 外では推奨 | Any HTTP runtime |
| VS Code extension helper flow | ChatGPT を接続する場合のみ | ChatGPT URL を copy する場合は使用 | ChatGPT では推奨 | VS Code-launched runtime |

参照： [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## 各 runtime が制御するもの

どの runtime も同じ server code を起動し、有効化された場合は同じ MCP tool family を公開します：

- Shell と persistent shell session。
- Filesystem、search、patch tools。
- Git operations。
- Playwright による browser automation。
- Audit log と task-state tools。
- Tokenized file links。
- Optional remote-worker lifecycle と machine-routed tools。

違うのは抽象 API ではなく、その背後の **operating environment** です。

| 質問 | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Command はどこで実行？ | container 内 | 通常 host workspace 上 | host または VM process environment |
| Default workspace は？ | Mounted `/workspace` | 現在の VS Code folder または設定 path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser は preinstall？ | 広く含まれる | host に install 済みのものだけ | host に install 済みのものだけ |
| Reset は容易？ | container と workspace volume を再作成 | workspace 次第 | host/VM 次第 |
| 任意 package install に適切？ | disposable なら適切 | host では risk が高い | VM 内でなければ risk が高い |

## 推奨選択

理由がなければまず **Docker Compose** を使用してください。最も明確な safety boundary と最も完全な標準 toolchain を提供します。

workflow が editor から始まり local launcher が必要なら **VS Code extension** を使います。これも runtime です。それだけで ChatGPT から到達可能になるわけではないため、ChatGPT web/app では tunnel または reverse proxy を追加してください。

Docker が使えず、VM/container host/dedicated user account が boundary を提供する場合は **standalone binary** を使います。

`local-shell-mcp` 自体の development/debug、または Python-based environment が管理しやすい場合は **`pipx` または source install** を使います。

server process を spawn できる local MCP client のみ **stdio mode** を使います。public deployment ではなく、ChatGPT web/app から直接は利用できません。

## Public endpoint のルール

ChatGPT のような HTTP MCP client では MCP endpoint は：

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` は origin のみです：

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` に `/mcp` を追加しないでください。

## Runtime ページ

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Client ページ

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
