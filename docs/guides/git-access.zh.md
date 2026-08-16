<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git 访问

`local-shell-mcp` 通过 `run_shell`、`shell_start` 或 `job_start` 使用标准 Git 命令行界面。项目有意不提供专用的 Git MCP wrapper：CLI 功能完整、coding agent 熟悉，而且可以避免在工具列表中重复实现每一个 Git 子命令。

## 常见工作流

尽可能使用有明确边界的非交互命令：

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

典型的 agent 流程如下：

1. 使用 `run_shell(command="git status --short --branch")` 检查状态。
2. 只读取和修改相关文件。
3. 运行针对性测试。
4. 使用 `run_shell(command="git diff --check && git diff")` 检查改动。
5. 提交或推送前运行 `secret_scan`。
6. 使用明确的 Git CLI 命令暂存、提交并推送。

如果仓库位于远程 worker 上，请在同一个 shell 工具中指定 `machine`。

## 凭据

Docker 部署可以在 `/persist/credentials` 下持久化常见 Git 凭据位置。应将该 volume 视为敏感数据。优先使用仓库范围的 deploy key、短期 GitHub App token、隔离的自动化账号，并在 push 前人工检查。

## Commit 规范

保持 commit 聚焦，不要包含生成的 cache 和 build artifact，记录执行过的测试，并避免暂存无关改动。对于 reset、clean、force-push 等破坏性命令，应先检查确切目标。

## 故障排查

`git push` 失败时，检查 remote URL、凭据持久化、branch protection 和 token 权限。安装了 GitHub CLI 时，`gh auth status` 很有帮助。
