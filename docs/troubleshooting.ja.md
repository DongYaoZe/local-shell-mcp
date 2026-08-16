<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# トラブルシューティング

サービスの正常性を確認します。

```bash
curl -i http://127.0.0.1:8765/healthz
```

ログを確認します。

```bash
docker compose logs --tail=100 local-shell-mcp
```

ChatGPT が接続できない場合は、`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` が実際の公開 HTTPS origin と完全に一致していること、および `/mcp`、OAuth メタデータ、`/healthz` が tunnel またはリバースプロキシ経由で到達可能であることを確認してください。

リモート worker が表示されない場合は、remote モードが有効であること、招待が期限切れでないこと、リモートマシンからコントロールサーバーへ外向き HTTPS リクエストを送信できることを確認してください。
