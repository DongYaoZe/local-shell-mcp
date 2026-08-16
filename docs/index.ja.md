<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">ChatGPT 対応 MCP control plane</span>

# local-shell-mcp

Chat を離れずに、AI assistant に制御された shell、実 workspace、Git、browser automation、file sharing、remote-worker access を提供します。

<div class="hero-actions" markdown>
[はじめる](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Runtime を選ぶ](guides/deployment.md){ .hero-action .hero-action--secondary }
[Tools reference](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### 実際の coding environment
1 つの MCP endpoint から tests の実行、repository の調査、file patch、Git 操作、audit trail の保持を行えます。
</div>

<div class="feature-card" markdown>
### Runtime と client のレイヤー
Docker、VS Code extension、binary、Python、stdio などの runtime を選び、その後 ChatGPT または別の MCP client を独立して接続します。
</div>

<div class="feature-card" markdown>
### Remote machine control
SSH port を開かず、outbound worker connection で NAT、firewall、HPC machine を接続します。
</div>
</div>

## 提供するもの

`local-shell-mcp` は制御された local/container workspace を ChatGPT や他の MCP client に公開します。Shell、persistent shell、filesystem、search、patch、Git、Playwright、audit、optional Goal Plan を持つ durable logical Session、tokenized file link、remote-worker tool を、OAuth 対応の ChatGPT-compatible MCP server から提供します。

AI が repository を調査し、tests を実行し、files を編集し、Git を操作し、browser evidence を収集し、downloadable artifacts を作成し、control server へ outbound 接続しかできない remote machine を制御する必要がある場合に使います。

## アーキテクチャ

```text
Runtime layer: Docker / VS Code extension / binary / Python / stdio
Exposure layer: localhost / HTTPS proxy / tunnel / stdio pipe
Client layer: ChatGPT / generic MCP client / editor helper
Controlled workspace: /workspace or configured workspace root
Optional remote workers: outbound machine connections
```

意図された isolation boundary は service を実行する container または VM です。

## シナリオ別の入口

| シナリオ | 開始ページ | 理由 |
|---|---|---|
| 初めての public ChatGPT deployment | [Quickstart](getting-started/quickstart.md) | OAuth と `/mcp` 設定を含む Docker Compose 手順 |
| runtime layer を選ぶ | [Runtime choices](guides/deployment.md) | Docker、VS Code、binary、Python、stdio を別々の runtime option として説明 |
| ChatGPT を client として追加 | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint、OAuth、最初の安全な prompt、tool discovery |
| LSM を DeepSeek Harness に追加 | [DeepSeek Harness plugin](clients/deepseek-harness.md) | この repository を DSH bundle として install し、完全な LSM tool/remote-worker surface を維持 |
| VS Code から実行 | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime と host safety の注意 |
| toolset の運用方法を学ぶ | [Usage patterns](guides/usage-patterns.md) | Prompt template と tool 選択ガイド |
| すべての tool を理解 | [Tools reference](reference/tools.md) | 各 tool の purpose、inputs、returns、combinations、notes |
| HPC、NPU/GPU、server node を接続 | [Remote workers](guides/remote-workers.md) | Outbound worker join flow と remote tool usage |
| 生成 file を共有 | [File links](guides/file-links.md) | TTL と revoke を備えた tokenized download URL |
| deployment を harden | [Security](security.md) | Isolation、OAuth、workspace scope、audit logs |

## 主な tool family

| Family | 例 | 用途 |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Build、tests、scripts、long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection と precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Review 可能な source-control workflow |
| Sessions と Goal | `session_manage`, `plan_manage` | durable task handoff、progress report、optional Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction、UI check、screenshot、rendered docs、page text |
| File links | `link_create`, `link_revoke` | Chat から generated artifacts を download |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | NAT、firewall、cluster login flow の背後にある machine |

## 代表的な workflow

### ChatGPT で coding

1. 専用 workspace で Docker Compose、VS Code extension、binary、Python などの runtime を開始します。
2. ChatGPT に network access が必要なら HTTP runtime を公開します。
3. Public `/mcp` endpoint を ChatGPT に追加します。
4. まず repository の調査と read-only checks を依頼します。
5. 承認されたら file patch、tests、diff review、commit、push を行わせます。
6. File link や remote system を扱う task では audit log を確認します。

### Remote HPC / accelerator host

1. 1 回限りの remote worker invite を作成します。
2. 生成された command を remote host に貼り付けます。
3. 通常の tools に `machine` を付け、Git は `run_shell`、path transfer は `remote_transfer` を使います。
4. Task 後に worker を revoke します。

### Artifact generation

1. AI に `/workspace` 下で file を生成させます。
2. TTL/download limit 付き tokenized file link を作ります。
3. Link を chat で共有します。
4. 完了したら revoke します。

## 言語

この site は native MkDocs i18n plugin で build されています。Header の language selector で English と translated pages を切り替えられます。翻訳版がないページは English に fallback します。
