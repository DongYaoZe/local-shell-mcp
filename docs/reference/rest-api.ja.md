<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

主要 interface は `/mcp` の MCP です。REST surface も health check、file link、および一部の service operation 向けに利用できます。

## ヘルスチェック

```http
GET /healthz
```

サーバーの正常性と基本的な状態を返します。

## MCP

```http
POST /mcp
```

ChatGPT およびその他の MCP client が使用する Streamable HTTP MCP endpoint です。

## REST 経由のツール呼び出し

REST のツール呼び出しは、成功時とエラー時で一貫した envelope を使用します。検証エラーはフレームワーク例外をそのまま返すのではなく、構造化された `ok: false` payload を返します。

## Agent Skills

固定の Skills registry は REST からも利用できます。

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill ディレクトリの変更は次の呼び出しで反映され、MCP ツール一覧は変化しません。

## ファイルリンク

トークン付きのファイルダウンロードは組み込み HTTP app から提供されます。リンクは bearer URL で、TTL、任意の最大ダウンロード回数、失効操作をサポートします。

## 認証

公開環境では OAuth を使用してください。開発時には localhost bypass を有効にできますが、認証なしで公開アクセスを許可するのは安全ではありません。
