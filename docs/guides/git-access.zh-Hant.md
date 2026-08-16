<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git 存取

`local-shell-mcp` 透過 `run_shell`、`shell_start` 或 `job_start` 使用標準 Git 命令列介面。專案刻意不提供專用的 Git MCP wrapper：CLI 功能完整、coding agent 熟悉，而且可避免在工具清單中重複實作每一個 Git 子命令。

## 常見工作流程

盡可能使用有明確邊界的非互動式命令：

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

典型的 agent 流程如下：

1. 使用 `run_shell(command="git status --short --branch")` 檢查狀態。
2. 只讀取與修改相關檔案。
3. 執行針對性測試。
4. 使用 `run_shell(command="git diff --check && git diff")` 檢查變更。
5. Commit 或 push 前執行 `secret_scan`。
6. 使用明確的 Git CLI 命令 stage、commit 並 push。

如果 repository 位於遠端 worker，請在同一個 shell 工具中指定 `machine`。

## 憑證

Docker 部署可在 `/persist/credentials` 下持久化常見 Git 憑證位置。應將該 volume 視為敏感資料。優先使用 repository 範圍的 deploy key、短期 GitHub App token、隔離的自動化帳號，並在 push 前人工檢查。

## Commit 規範

保持 commit 聚焦，不要包含產生的 cache 與 build artifact，記錄執行過的測試，並避免 stage 無關變更。對 reset、clean、force-push 等破壞性命令，應先檢查確切目標。

## 疑難排解

`git push` 失敗時，檢查 remote URL、憑證持久化、branch protection 與 token 權限。若已安裝 GitHub CLI，`gh auth status` 很有幫助。
