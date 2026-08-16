<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git アクセス

`local-shell-mcp` は `run_shell`、`shell_start`、`job_start` を通じて標準の Git CLI を使用します。専用の Git MCP wrapper は意図的に公開していません。CLI は完全で coding agent に馴染みがあり、Git の全サブコマンドをツール一覧に重複実装する必要がないためです。

## 一般的なワークフロー

可能な限り、範囲を限定した非対話コマンドを使います。

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

典型的な agent の手順：

1. `run_shell(command="git status --short --branch")` で状態を確認します。
2. 関連ファイルだけを読み取り、編集します。
3. 対象を絞ったテストを実行します。
4. `run_shell(command="git diff --check && git diff")` で差分を確認します。
5. commit または push 前に `secret_scan` を実行します。
6. 明示的な Git CLI コマンドで stage、commit、push します。

repository が remote worker 上にある場合は、同じ shell tool に `machine` を指定します。

## Credential

Docker deployment では、一般的な Git credential の保存場所を `/persist/credentials` 配下に永続化できます。この volume は機密情報として扱ってください。repository-scoped deploy key、短命の GitHub App token、隔離された automation user を優先し、push 前に手動 review を行ってください。

## Commit hygiene

commit は論理的な変更に集中させ、生成 cache や build artifact を含めず、実行した test を記録し、無関係な変更を stage しないでください。reset、clean、force-push などの破壊的 command では、対象を正確に確認してから実行します。

## トラブルシューティング

`git push` が失敗する場合は remote URL、credential persistence、branch protection、token permission を確認します。GitHub CLI が入っている場合は `gh auth status` が役立ちます。
