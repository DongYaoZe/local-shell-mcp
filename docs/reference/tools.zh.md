# 工具参考

本页概述 `local-shell-mcp` 当前公开的 MCP 工具。英文参考页由实际 MCP Schema 自动生成，包含每个参数的类型和默认值。

公开工具返回包含 `ok`、`message`、`data` 的结构化结果；`workspace_open` 返回用于渲染 MCP App 的模型可见状态。多数执行、文件和浏览器工具都接受可选的 `machine` 参数：省略时在控制端执行，指定时在对应远程 worker 执行，并额外要求 `remote:use` 权限。

Git 不再拥有专用 MCP 工具。请通过 `run_shell` 执行标准 Git CLI，例如 `git status --short --branch`、`git diff`、`git commit` 和 `git push`。

## 工具分组

### Live Workspace

`workspace_open`


### 环境、Skills 与任务状态

`environment_get`、`skill_list`、`skill_load`、`skill_read`、`secret_scan`、`session_manage`、`plan_manage`、`audit_tail`

`environment_get` 已包含运行版本、Python、平台、可执行文件、工作区、权限策略和基础探测信息，因此不再单独暴露 `version_info`。

### Shell 与长期任务

`run_shell`、`run_python`、`shell_start`、`shell_send`、`shell_read`、`shell_stop`、`shell_list`、`job_start`、`job_list`、`job_tail`、`job_stop`、`job_retry`

- 短期、非交互命令使用 `run_shell`。
- 需要交互的终端、REPL、TUI 使用 `shell_*`。
- 需要可跟踪、停止和重试的长期任务使用 `job_*`。

### 文件、搜索与传输

`file_list`、`file_tree`、`file_glob`、`file_grep`、`file_read`、`image_view`、`file_write`、`file_edit`、`file_delete`、`file_patch`、`remote_transfer`

- `file_read.path` 可以是单个路径，也可以是路径数组。
- `file_edit.edits` 接受一个或多个精确替换项，不再区分单次与批量编辑工具。
- `remote_transfer` 自动判断源是文件还是目录，并立即创建一个可跟踪的传输 job，支持控制端到 worker、worker 到控制端以及 worker 到 worker。使用 `job_list`、`job_tail`、`job_stop` 和 `job_retry` 查看、停止或重试；worker 到控制端的上传使用可续传的原始二进制分块。`source_machine` 或 `destination_machine` 至少指定一个。

### 浏览器自动化

`browser_session`、`browser_snapshot`、`browser_act`、`browser_run_script`

- 常规页面检查、文本读取和截图优先使用 `browser_session`、`browser_snapshot` 与 `browser_act`。
- JavaScript 求值、自定义截图/PDF 和复杂流程由 `browser_run_script` 执行完整 Playwright 脚本。
- 浏览器安装使用普通 shell 命令，不再长期占用独立工具入口。

### 文件下载链接

`link_create`、`link_list`、`link_revoke`

链接使用高熵 bearer token，并支持 TTL、下载次数限制和主动撤销。

### 远程 worker 管理

`remote_manage`

只有 worker 管理继续使用 `remote_*` 名称。实际执行使用普通工具及其 `machine` 参数。

## 常用流程

| 需求 | 推荐工具 |
|---|---|
| 检查环境 | `environment_get` → `file_tree` → `file_read` |
| Git 操作 | `run_shell` 执行标准 Git CLI |
| 精确修改文件 | `file_read` → `file_edit` / `file_patch` → 测试与 `git diff` |
| 长时间任务 | `job_start` → `job_tail` → `job_stop` / `job_retry` |
| 远程执行 | 同一工具增加 `machine` |
| 跨机器传输 | `remote_transfer` |
| 浏览器证据 | `browser_snapshot` / `browser_run_script` |
