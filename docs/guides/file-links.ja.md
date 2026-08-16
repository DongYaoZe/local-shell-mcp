<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# ファイルリンク

`local-shell-mcp` は、制御された workspace のファイルを高エントロピーの bearer URL で公開できます。AI が生成した report、archive、PDF、screenshot などの artifact を chat からダウンロードまたは表示する必要がある場合に便利です。

## ファイルリンクを使う場面

ファイルリンクは次の用途に使用します。

- 生成した PDF や report。
- Screenshot と browser artifact。
- Build output。
- Chat に貼るには大きすぎる log。
- 手動確認用に準備した archive。

secret、private key、credential store、無関係な個人データにはファイルリンクを使用しないでください。

## 一般的な流れ

1. `/workspace` 配下でファイルを生成または見つけます。
2. TTL と任意の download limit を指定して `link_create` を呼び出します。ファイルをブラウザーや Markdown image で直接表示したい場合は `inline=true` を指定します。既定は `false` で、attachment download になります。
3. 返された URL を共有します。
4. 不要になったらリンクを revoke します。

## 関連ツール

| Tool | 用途 |
|---|---|
| `link_create` | Workspace file 用の tokenized URL を作成します。 |
| `link_list` | 有効なリンクを表示します。 |
| `link_revoke` | Expiry 前にリンクを無効化します。 |

## 制御項目

設定オプションには次が含まれます。

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

機密性の高い artifact には短い TTL を使用し、単一の受信者向けリンクでは maximum download count を設定してください。

## セキュリティ上の注意

ファイルリンクは bearer URL です。URL を知っている人は、期限切れ、download limit 到達、または revoke されるまでファイルをダウンロードできます。一時的な secret と同様に扱ってください。Inline response には CSP sandbox と `X-Content-Type-Options: nosniff` が含まれるため、active format が LSM origin にアクセスしたり、sandbox なしで same-origin content として実行されたりすることを防ぎます。
