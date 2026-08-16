<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT コネクタ

このページでは client 接続としての ChatGPT を扱います。runtime はここでは選びません。このページを使う前に Docker、VS Code extension、binary、または Python install でサーバーを起動してください。

`local-shell-mcp` は ChatGPT Developer Mode と完全な MCP client 向けに設計されています。MCP endpoint は通常の LSM tool surface を直接公開します。

## Runtime の前提条件

まず runtime を 1 つ選んで起動します：

| Runtime | ページ |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

次に ChatGPT から到達できる network path でその runtime を公開します。詳細は [network connectivity](../clients/connectivity.md).

## 公開 URL

ChatGPT は HTTPS 経由でサーバーに到達する必要があります。MCP endpoint は：

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` が public origin と一致することを確認します：

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` に `/mcp` を含めないでください。

## OAuth 設定

公開環境で推奨する設定：

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

長い coding session は短い token lifetime を超えることがあるため、access token は既定では期限切れになりません。必要に応じて JWT secret を rotate するか、新しい state で再 deploy して access を revoke してください。

## コネクタを追加

1. ChatGPT の connector または Developer Mode MCP settings を開きます。
2. Custom MCP server を追加します。
3. MCP URL を入力します： `https://your-public-host.example.com/mcp`.
4. OAuth を完了します。
5. Tool surface を承認します。

## Live Workspace MCP App

MCP Apps をサポートする ChatGPT client は `local-shell-mcp` を対話型 execution workspace として表示できます。リアルタイムの可視性や人間との共同作業が役立つときに ChatGPT に Live Workspace を 1 回開かせてください。その後 app は `workspace_open` を繰り返し呼ばなくても自動で再接続します。

Live Workspace は意図的にモデルの reasoning から分離されています。観測可能な execution state と共有 resources を表示します：

- **Activity** は MCP tool の開始、完了、失敗、人間の操作を表示します。
- **Terminal** は既存の persistent shell backend に接続し、live PTY output を表示します。
- **Files** は local/remote workspace file の閲覧、preview、edit、create、delete を行います。
- **Diff** は staged/unstaged Git changes を表示し、現在の diff をレビュー用に ChatGPT へ送り返せます。
- **Jobs** は managed jobs と persistent sessions を表示します。
- **Remotes** は workers を表示し、remote support が有効な場合は invite、rename、revoke 操作を提供します。
- **Audit** は最近の structured MCP audit records を表示します。

Live Workspace は常に collaborative です。ChatGPT と人間が同じ workspace を同時に変更できます。host が対応する場合は floating PiP-style window で開き、fullscreen と windowed 表示を切り替えられます。独立した observe/takeover state はありません。

File、diff、audit、activity view は、選択した operational context を MCP Apps bridge 経由で次の model turn に送れます。これは明示的に共有される context であり、UI が private model reasoning を公開または再構成することはありません。

### ネットワークとセキュリティ

表示された MCP App は低遅延の terminal/event traffic のため、sandbox から設定済み service origin に直接接続します。そのため `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` は ChatGPT browser から到達できる HTTPS origin でなければなりません。MCP endpoint 自体は `https://your-public-host.example.com/mcp` のままです。

Workspace を開くと、ランダムで短寿命の Live Workspace bearer token が発行されます。この token は rendered app 向けの MCP result metadata だけに含まれ、model-visible structured content には入らず、human/live UI API だけが受け付けます。同じ `live_id` への自動再接続では現在の credential を再利用するため、再接続した view 同士が無効化し合いません。さらに現在の logical `session_id` も引き継ぐため、メモリ上の Live Workspace state が失われても durable Session を復元できます。明示的に新しい `workspace_open` を呼ぶと credential がローテーションされます。embedded app は browser cookie や ambient credential を使いません。

MCP Apps を実装しない client は UI metadata を無視できます。通常の MCP data tools はすべて引き続き利用でき、動作も変わりません。

## 最初の prompt

```text
local-shell-mcp を使用してください。まず environment_get を呼び出し、その後 workspace root を一覧してください。まだファイルを変更しないでください。
```

これにより変更を加えず connectivity を確認できます。

## 推奨運用ルール

モデルには明確な制約を与えてください：

- 明示されない限り `/workspace` 内で作業する。
- commit 前に tests を実行する。
- push 前に `secret_scan` を使う。
- 共有して安全な file にだけ `link_create` を使う。
- 長時間 process では persistent shell session を優先する。
- file を変更した command をすべて要約する。

## Tool discovery の問題

ChatGPT が認証できても想定した tools が表示されない場合：

- endpoint が `/mcp` で終わることを確認します。
- `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY` を確認します。
- reverse proxy headers と request body limits を確認します。
- `docker compose logs --tail=200 local-shell-mcp` を確認します。
- service が `mcp` または `both` mode であることを確認します。

## 安全上の注意

公開 deployment では OAuth を有効にしてください。認証なしの完全な MCP tools を public internet に公開しないでください。承認した各 tool は connected model の実効権限の一部として扱ってください。
