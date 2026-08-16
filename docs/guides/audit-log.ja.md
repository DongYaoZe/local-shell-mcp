<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

ログの上限は `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` です。長期間保持する必要がある場合は、rotation または外部への export を行ってください。

## 制限

監査ログは sandbox ではありません。追跡性は向上しますが、接続したモデルが設定された権限内で操作することを防止するものではありません。
