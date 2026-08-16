<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# VS Code extension runtime

VS Code extension は同じ `local-shell-mcp` server の launcher と convenience UI です。現在の editor workspace 用に server process を起動するため、runtime の選択肢です。

ChatGPT connector 自体ではありません。ChatGPT web/app から使う場合、ChatGPT は引き続き public HTTPS `/mcp` endpoint に接続します。

## Extension が行うこと

Extension は：

- 現在の VS Code workspace 用に `local-shell-mcp` を開始します。
- Server を stop/restart します。
- VS Code output channel に server output を表示します。
- `/healthz` を確認します。
- MCP URL を copy します。
- Workspace と endpoint を含む ChatGPT setup prompt を copy します。

Extension は server binary を bundle しません。`local-shell-mcp` を別途 install し、`PATH` にない場合は extension に executable path を設定してください。

## 使う場面

次の場合にこの runtime を使います：

- 普段 VS Code folder から作業を始める。
- terminal command を手動で起動する代わりに button/command-palette flow が欲しい。
- Project dependencies が既に host に install されている。
- Trusted repository または狭い workspace を扱う。
- その workspace だけを model に公開することに同意できる。

次の場合は Docker を使います：

- Repository が untrusted。
- Task が arbitrary packages を install する。
- 幅広い preinstalled toolchain が必要。
- Container 再作成で簡単に reset したい。
- Host account より明確な boundary が必要。

## Executable を install

Server install method を 1 つ選びます：

```bash
pipx install local-shell-mcp
```

または OS 用 release binary を download して `PATH` に置きます。

次に VSIX release asset を install します：

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

または command palette の **Extensions: Install from VSIX...** を使用します。

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | MCP に公開する workspace | 最初の VS Code folder なら empty、または explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Prompt/URL に copy される public HTTPS origin | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | OAuth authorization 用 PIN | Public use では strong random value |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Direct host usage では `false` を維持 |
| `local-shell-mcp.extraEnv` | Server process の extra environment | Project-specific safe values のみ |

## 基本 flow

1. VS Code で project folder を開きます。
2. **local-shell-mcp: Start Server** を実行します。
3. 利用できる場合は **Show Server Status** または **Check Health** を実行します。
4. Local MCP client 用に **Copy MCP URL**、ChatGPT 用に **Copy ChatGPT Setup Prompt** を実行します。
5. Endpoint を client に追加します。

Local endpoint は通常：

```text
http://127.0.0.1:8765/mcp
```

これは local client には使えますが ChatGPT web/app からは到達できません。

## ChatGPT と使う

VS Code-launched server を ChatGPT から使うには local port の前に HTTPS tunnel または reverse proxy を置きます。

例：

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

設定：

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

ChatGPT 用に copy する URL は `/mcp` で終わります：

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Extension は通常 host user 権限で command を実行します。これは disposable Docker container と本質的に異なります。

推奨ルール：

- Model に control させる repository だけを開く。
- `allowFullContainer` は無効のままにする。
- Workspace root を home directory にしない。
- 無関係な secrets を workspace に置かない。
- Commit/push 前に `secret_scan` を使う。
- Unfamiliar repository や package-install-heavy task では Docker を優先する。

## 一般的な prompt

Setup prompt を copy した後、read-only task から始めます：

```text
local-shell-mcp を使用してください。まず environment_get と workspace に対する file_tree を呼び出してください。まだファイルを変更しないでください。
```

次に bounded edit へ進みます：

```text
この workspace の failing test を修正してください。まず relevant files を読み、最小 patch を作成し、targeted test を実行して git diff を表示してください。承認するまで commit しないでください。
```

## Troubleshooting

| 症状 | 確認項目 |
|---|---|
| Extension が server を起動できない | `local-shell-mcp.executablePath` が存在し terminal で `--help` が動くか確認 |
| ChatGPT から到達できない | Local `127.0.0.1` URL は public ではないため tunnel/proxy と `publicBaseUrl` を設定 |
| Tools が間違った folder を公開 | `local-shell-mcp.workspaceRoot` を明示設定 |
| Restart 後 auth が失敗 | `extraEnv` または runtime configuration で stable OAuth admin PIN と JWT secret を設定 |
| Commands に dependencies がない | Host に dependencies を install するか Docker runtime に切り替える |
