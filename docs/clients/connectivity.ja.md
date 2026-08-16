<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# ネットワーク接続

マシンの外部にある HTTP MCP client から接続するには、到達可能な HTTPS origin が必要です。このページではネットワーク経路を扱い、どの runtime を選ぶかは扱いません。

client endpoint は通常 `/mcp` で終わります。

```text
https://your-public-host.example.com/mcp
```

サーバーの public base URL 設定には origin だけを指定します。

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

この base URL に `/mcp` を含めないでください。

## 接続方法

| 方法 | 使用する場面 |
|---|---|
| Compose tunnel sidecar | 組み込みの `tunnel` profile を使う Docker Compose |
| 外部 tunnel | ローカルネットワーク外から到達させる必要がある任意の runtime |
| Caddy | 自動 TLS を簡単に使いたい場合 |
| Nginx / Nginx Proxy Manager | 既存の Nginx インフラがある場合 |
| Traefik | 既存のコンテナネイティブなルーティングがある場合 |

## パス

origin 全体を実行中のサーバーへ転送してください。重要なパスは次のとおりです。

| パス | 用途 |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | ヘルスチェック |
| `/.well-known/...` | client discovery メタデータ |
| `/oauth/...` | client 認可フロー |
| `/downloads/...` | 任意の生成ファイルリンク |
| `/join/...`, `/remote/...` | 任意の remote-worker フロー |

## プロキシの動作

プロキシはパスを保持し、request body を転送し、長時間の response を許可し、極端に短い timeout を避ける必要があります。

## 確認

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## よくある間違い

| 間違い | 修正 |
|---|---|
| ChatGPT で `https://host/mcp` ではなく `https://host` を使う | client endpoint にだけ `/mcp` を追加する |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` と設定する | origin だけを設定する |
| `/mcp` だけをルーティングする | discovery と認可パスも動作するよう origin 全体をルーティングする |
| host runtime で広すぎる workspace を使う | 狭い workspace または Docker を使う |

## 推奨の組み合わせ

| Runtime | ネットワーク構成 |
|---|---|
| サーバー上の Docker Compose | 既存の reverse proxy または Compose tunnel profile |
| 自宅マシン上の Docker Compose | outbound tunnel |
| ノート PC 上の VS Code extension | セッション中だけの一時 tunnel |
| VM 上の binary | VM またはネットワーク境界の reverse proxy |
| Python/source 開発サーバー | 通常は localhost のみ |
| Stdio mode | HTTP 経路なし。ローカル MCP client を使う |
