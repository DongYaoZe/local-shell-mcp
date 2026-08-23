<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# 監査ログ

`local-shell-mcp` は、接続した client が行った操作を再構成できるよう、構造化された監査エントリを書き込みます。

既定のパス：

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## 記録される内容

監査エントリには、次のようなイベントが含まれます。

- Tool call の開始/終了。
- コマンド実行メタデータ。
- Timeout と処理済みエラー。
- Remote worker の登録と job activity。
- File-link の作成と失効。
- 該当する認証関連イベント。

サーバーが識別できる機密引数は redaction されます。

## ログの読み取り

MCP tool を使います。

```text
audit_tail
```

または直接確認します。

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## 運用上の用途

監査ログは特に次の用途に役立ちます。

- ファイルを変更したコマンドの確認。
- Remote worker が使用されたかの確認。
- 予期しない失敗のデバッグ。
- File link の誤公開の検出。
- 公開 deployment の設定ミス後の incident response 支援。

## 保持期間

アクティブな `audit.jsonl` は、既定で `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` により 20 MB に制限されます。保持処理では古いレコードを破棄せず、自己完結型の Zstandard アーカイブ `audit-archive/*.jsonl.zst` に移動します。外部化された大きな audit payload も、hot store から削除する前にアーカイブへ格納されます。

圧縮アーカイブは `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` で別途制限され、既定値は 512 MB です。上限を超えると最古のアーカイブから削除されます。`0` に設定すると長期圧縮保持を無効化できます。通常の最近の照会は hot log のみを読み、履歴が必要な場合にだけアーカイブを参照します。

## 制限

監査ログは sandbox ではありません。追跡性は向上しますが、接続したモデルが設定された権限内で操作することを防止するものではありません。
