<!-- i18n-source-sha256: 8c683835be3adb3bf08d9d69b1731f61a39753bf255170fc663cf9456a0df54f -->
# ヒューマンインターフェース

`local-shell-mcp` は、同じ service API、workspace、persistent terminal registry、remote-worker registry、MCP audit log の上に、互換性のある2つの human interface を提供します。

- **Web UI** は、運用状態を素早く確認するために最適化されたネイティブブラウザーダッシュボードです。
- **OpenTUI** は完全なターミナル指向アプリケーションで、ブラウザー内とネイティブターミナルコマンドの両方で利用できます。

どちらの mode も別の control plane を作りません。interface を切り替えても、接続済み machine、Session、job、permission、audit data は変わりません。

## サービスを起動する

通常どおり `local-shell-mcp` を起動します。

```bash
local-shell-mcp --mode mcp
```

## ChatGPT Live Workspace

ChatGPT が MCP Apps を描画できる場合、`workspace_open` は現在 attach されている logical Session の floating collaborative view を開きます。durable task state は Session が所有し、Live Workspace は live activity と human controls の表示だけを担当します。そのため App の reconnect や ChatGPT/MCP transport の変更で Session はリセットされません。

典型的な handoff は次のとおりです。

```text
session_manage(action="start", objective=...)
        -> session_id
... tool work + session_manage(action="report", ...) ...
new agent run
session_manage(action="resume", session_id=..., takeover=true)
        -> inherited progress, Plan, and recent activity
workspace_open()
        -> reconnectable view of that Session
```

`takeover=true` はまだ active な古い agent run を supersede します。supersede された run からの後続 tool call は、その agent が明示的に Session を再び resume するまで拒否されます。Session は machine や working directory に bind されず、通常の tool parameter が引き続き local/remote target と path を選びます。

optional な `plan_manage` Plan は Session の Goal mode を有効にします。Plan が active で agent activity が15分ない場合、attach 済み Live Workspace は ChatGPT に continuation を要求できます。continuation は同じ `session_id` を先に resume し、accepted/rejected を問わず最大10回です。blocked/completed/cancelled Plan は自動 continuation されません。全 step が completed/skipped の active Plan は cleanup continuation の対象に残り、resumed agent が Plan を正式に finish できます。human pause/resume/cancel controls は一時的な Live Workspace state ではなく Session-owned Plan を更新します。

## ブラウザーインターフェース

開く URL：

```text
http://127.0.0.1:8765/ui
```

公開デプロイでは、設定済みの HTTPS origin を使用します。

```text
https://your-public-host.example.com/ui
```

ブラウザーインターフェースは MCP と同じ OAuth サーバーと scope を使用します。ログイン画面を読み込めるようページシェルと静的アセットは公開されていますが、`/api/ui/*` と OpenTUI ターミナル WebSocket は引き続き保護されます。アクセストークンはブラウザーの session storage にのみ保存されます。

### インターフェースを選ぶ

OAuth 画面には 2 つの入口があります。

- **Open Web UI** は認可してネイティブダッシュボードを開きます。
- **Continue to OpenTUI** は認可してターミナルインターフェースを開き、従来のブラウザー動作を維持します。

認可後は、サイドバーのインターフェースセレクターで再ログインせず Web UI と OpenTUI を切り替えられます。一時的に OpenTUI に移動した場合も、現在のネイティブページは記憶されます。

各ルートはブックマークできます。

```text
/ui/#/overview
/ui/#/machines
/ui/#/workloads
/ui/#/activity
/ui/#/console
```

`#/web` と `#/dashboard` は Overview の別名、`#/tui` と `#/opentui` は Console の別名です。

## ネイティブ Web UI

ネイティブ Web UI は既存のヒューマンインターフェース API を 5 秒ごとにポーリングし、ターミナルセルではなくブラウザーネイティブのコントロールを描画します。OpenTUI を選択するまで PTY は起動しません。

### Overview

Overview は優先度の高い運用情報から表示します。

- Controller のヘルスと現在の LSM バージョン。
- オンライン／オフラインのマシン数。
- 実行中の tracked job と永続ターミナルセッション。
- CPU、メモリ、ワークスペースディスク、load、ネットワークスループット、uptime。
- worker 状態、リソースしきい値、失敗した job、失敗した MCP 呼び出しから生成されたアラート。
- 最近のモデル起点 MCP アクティビティ。

### Machines

Machines はローカル controller と接続済みのリモート worker を一覧し、状態、プラットフォーム、バージョン、作業ディレクトリ、機能、last-seen 情報を表示します。

### Workloads

Workloads は実行中の tracked job と独立した永続 shell セッションをまとめて表示します。Web UI ではこれらのレコードは読み取り専用で、対話的なセッション管理には OpenTUI を使用します。

### Activity

Activity は現在のアラートと最近の MCP 監査アクティビティをまとめます。人間が入力したコマンドやファイル操作は MCP 監査ログには含まれません。

## ブラウザー OpenTUI

**OpenTUI** を選択すると、ネイティブターミナルランチャーと同じ OpenTUI アプリケーションが遅延起動します。ブラウザー console には次の機能があります。

- WebSocket 上の認証済みバイナリ PTY 転送。
- ターミナルの自動リサイズと再接続バックオフ。
- OpenTUI コントロールへのマウス操作。
- フルスクリーンモードとブラウザー安全なキーボードショートカット。
- モバイル向けショートカットキーと明示的なソフトキーボード制御。
- xterm.js による SIXEL と inline image のサポート。

ユーザーがネイティブ Web UI モードにいる間、ブラウザーは OpenTUI PTY を作成しません。

## ネイティブ OpenTUI

スタンドアロン release 実行ファイルにはプラットフォーム用 OpenTUI runtime が組み込まれています。メイン実行ファイルだけを保持し、サービスを起動してから次を実行します。

```bash
local-shell-mcp tui
```

ネイティブ TUI は人間のオペレーターにログインを要求しません。ランチャーが生成したローカル資格情報を loopback API に透過的に渡します。この資格情報は設定済み state directory に owner のみが読める権限で保存され、loopback から接続するリバースプロキシには bypass は与えられません。

ソース checkout でも Bun 依存関係をインストールすれば TUI を実行できます。

```bash
cd ui
bun install --frozen-lockfile
bun run build
cd ..
local-shell-mcp tui
```

ローカルサービスがデフォルト以外のポートを使う場合だけ `--api-base` を使用します。

```bash
local-shell-mcp tui --api-base http://127.0.0.1:9876/api/ui
```

## OpenTUI 画面

### Dashboard

Dashboard は OpenTUI の運用概要です。幅の広いターミナルでは node、workload、alert、activity、システム情報、trend の領域を分けて表示し、狭いターミナルでは横スクロールなしのコンパクトな要約に畳みます。

### Files

Files はローカル／リモートマシン向けの LSM ネイティブ 3 ペインファイルマネージャーです。作成、編集、名前変更、コピー、移動、貼り付け、削除、隠しファイル切替、更新、テキストプレビュー、バイナリプレビュー、サイズ制限付き画像サムネイルを提供します。

### Terminals

Terminals はローカル／リモートマシン上の永続 shell セッションを管理します。完全なコマンド入力、raw 対話入力、セッション切替、作成と終了、最近の出力、折りたたみ可能な MCP 監査レールをサポートします。

### Audit

Audit は有界 JSONL 監査ログを読み取り、node、operation、event、session、search、time-range、sort フィルターとレコード詳細表示を提供します。

### Remotes

Remotes はオンライン／オフラインのリモート worker、機能、作業ディレクトリ、システムメタデータを表示します。1 回限りの join invite の作成、node 名変更、永続 identity の revoke ができます。

## OpenTUI ナビゲーション

上部カテゴリーバーと状況依存フッター操作は、ネイティブターミナルとブラウザー console の両方でマウスクリックできます。

| キー | 操作 |
|---|---|
| `Alt+1` … `Alt+5` | Dashboard、Files、Terminals、Remotes、Audit を開く。 |
| `F2` … `F6` | 代替カテゴリ shortcut。 |
| `F1` | キーボードガイドを開く。 |
| `F9` | マシン一覧を更新する。 |
| `Alt+Q` | ブラウザー予約の Ctrl ショートカットを呼び出さずネイティブ OpenTUI プロセスを終了する。 |

Terminals では `Alt+N` で新規セッション、`Alt+W` で選択セッションの終了、`Alt+A` で監査レール切替、`Alt+R` で更新、`Alt+Left/Right` でセッション切替を行います。ブラウザー console は、ブラウザーレベルのナビゲーションやメニュー処理より先にこれらのキーを捕捉します。

## 設定

| YAML key | 環境変数 | デフォルト | 用途 |
|---|---|---|---|
| `ui_enabled` | `LOCAL_SHELL_MCP_UI_ENABLED` | `true` | ヒューマンインターフェースをマウントまたは無効化する。 |
| `ui_path` | `LOCAL_SHELL_MCP_UI_PATH` | `/ui` | MCP サービス上のブラウザーインターフェースのマウントパス。 |
| `ui_tui_command` | `LOCAL_SHELL_MCP_UI_TUI_COMMAND` | auto | ネイティブ OpenTUI 実行ファイルの解決を上書きする。 |
| `ui_wallpaper` | `LOCAL_SHELL_MCP_UI_WALLPAPER` | `bing` | OpenTUI ブラウザー console デプロイ向けに保持される壁紙設定。 |
| `ui_terminal_idle_timeout_s` | `LOCAL_SHELL_MCP_UI_TERMINAL_IDLE_TIMEOUT_S` | `3600` | 非アクティブなブラウザー OpenTUI PTY をこの秒数後に閉じる。`0` で無効。 |
| `ui_terminal_max_sessions` | `LOCAL_SHELL_MCP_UI_TERMINAL_MAX_SESSIONS` | `8` | ブラウザー OpenTUI PTY の最大同時セッション数。 |

## パッケージング上の注意

- Docker イメージには Web UI アセットとネイティブ OpenTUI runtime が含まれます。
- スタンドアロン実行ファイルには Web UI アセットと圧縮されたプラットフォーム OpenTUI runtime が組み込まれます。
- Python wheel にはブラウザーアセットが含まれます。ネイティブ OpenTUI には release 実行ファイル、または Bun 依存関係を導入したソース checkout が必要です。
- 両インターフェースは MCP と同じプロセスとポートから提供され、追加の Web サービスは不要です。
