<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Stdio mode は、`local-shell-mcp` を child process として起動し、標準入力/標準出力で通信するローカル MCP client 向けです。

これは公開 HTTP deployment ではありません。ChatGPT はユーザーのマシン上で process を起動できないため、ChatGPT web/app から直接使用することはできません。

## stdio を使う場面

次の場合に stdio mode を使用します。

- MCP client が command-based server definition をサポートしている。
- client と制御対象 workspace が同じマシン上にある。
- OAuth、公開 HTTPS、reverse proxy、tunnel が不要。
- server lifecycle を client に管理させたい。

次の場合は stdio mode を使用しないでください。

- client が ChatGPT web/app。
- 複数の remote client が同じ server を必要とする。
- HTTP 経由の tokenized file download が必要。
- HTTP で提供される remote-worker join route が必要。

## コマンド

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

一般的な MCP client 設定には通常、次のような内容が含まれます。

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

schema は client に合わせて調整してください。`servers`、`tools`、`mcpServers`、`contextServers` などの名前を使う client があります。

## HTTP mode との動作差

| 項目 | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | なし | `/mcp` |
| OAuth | 不要 | 公開利用では推奨 |
| Health endpoint | なし | `/healthz`, `/readyz` |
| 公開 ChatGPT からの利用 | 不可 | HTTPS の背後で可能 |
| Server lifecycle | client が process を起動 | process/runtime を自分で管理 |

それ以外の tool surface は、configuration と client support の範囲内で同じ server-side implementation を使用します。

## 安全上の注意

Stdio mode は多くの場合 MCP client と同じ user で host 上に直接実行されます。workspace root を狭くし、広範な filesystem access は避けてください。stdio 自体が破棄可能な container/VM 内で実行されている場合を除き、full-container mode は無効のままにしてください。
