<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# 汎用 MCP client

`local-shell-mcp` は ChatGPT だけでなく、その他の MCP client からも利用できます。client は HTTP で接続するか、stdio 経由でサーバープロセスを起動するかを選びます。

## HTTP MCP client

サーバーが既に実行中の場合は HTTP mode を使用します。

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

ローカル endpoint：

```text
http://127.0.0.1:8765/mcp
```

ネットワーク endpoint：

```text
https://your-public-host.example.com/mcp
```

信頼された localhost の外から到達できる endpoint には OAuth を使用してください。

## Stdio MCP client

client 自身がサーバープロセスを起動する場合は stdio mode を使用します。

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

一般的な client 設定の形：

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

client ごとに schema は異なります。このセクションを `mcpServers` と呼ぶものもあれば、別の名前を使うものもあります。

## 最初の安全な確認

新しく接続した client では、次から始めます。

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

その後、編集・テスト・Git のルールを明示した、範囲を限定したタスクを実行してください。
