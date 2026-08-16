<!-- i18n-source-sha256: 9e104b7a893f61206aea6ed76b78bb04387fc5349535c46ffafd8f2e4c9ccd3e -->
# 工具参考

本页由实际 MCP tool schema 生成。公开工具接口变更后，运行 `python scripts/generate-tools-reference.py` 更新 English 参考页。

大多数工具返回包含 `ok`、`message` 和 `data` 的结构化 `ToolResult`。`workspace_open` 返回用于渲染 MCP App 的模型可见状态。多数执行和文件工具接受可选 `machine`；省略时操作 controller workspace，指定时操作已连接 worker。Git 操作有意通过 `run_shell` 或其它 shell 工具执行，而不提供专用 Git wrapper。

## 选择指南

| 需求 | 推荐工具 |
|---|---|
| 在 ChatGPT 中监控执行或协作 | `workspace_open` |
| 检查环境 | `environment_get`, `file_tree`, `file_read` |
| 运行短命令或 Git 操作 | `run_shell` |
| 运行交互式或长任务 | `shell_start` or `job_start` |
| 精确修改文件 | `file_edit` or `file_patch` |
| 传输文件或目录 | `remote_transfer` |
| 发现外部 MCP capability | `mcp_tool_search`, then `mcp_tool_inspect` |
| 与页面交互 | `browser_session`, `browser_snapshot`, then `browser_act` |
| 运行自定义 browser 逻辑 | `browser_run_script` |
| 在远程机器工作 | 使用同一工具并提供 `machine`；仅 worker 管理使用 `remote_*` |

## 交互式 workspace

### `workspace_open`

打开或复用交互式 Live Workspace，支持人类与 agent 实时协作。Active task 只需调用一次，后续复用会自动重连的浮动 workspace，而不要反复重新打开；当 terminal output、files/diffs、jobs、remotes 或 audit activity 能显著改善工作流时使用。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `cwd` | `string` | `"."` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

## 环境、Skills 与任务状态

### `environment_get`

返回本地或 remote machine 的版本、workspace、认证、策略与环境信息。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `skill_list`

列出已安装的 Agent Skills，但不加载其完整 instructions。MCP tool surface 保持固定；Skill directory 的新增或删除会在下一次调用时反映。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_load`

按 `skill_list` 返回的精确名称加载一个已安装 Skill，返回完整 `SKILL.md` instructions 与 related file paths。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_read`

读取一个已安装 Skill 的 related text file。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `name` | `string` | required |  |
| `path` | `string` | required |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `secret_scan`

在 commit 或 push 前扫描 local workspace 文本文件中的常见 secrets。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `max_results` | `integer` | `200` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `session_manage`

管理与机器和 cwd 无关的持久 logical task Session。实质性工具工作前先 start；在有意义的检查点 report 语义进度；新 GPT/MCP run 可按 `session_id` resume 接手。`resume(takeover=true)` 总会创建新的 agent run 并取代旧 run。后续 report/finish/cancel 和其它工具使用返回的 `active_run.run_id` 作为 `session_run_id`。动作：start、resume、get、report、list、finish、cancel、delete。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `action` | `string` | required |  |
| `session_id` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` |  |
| `label` | `string \| null` | `null` |  |
| `objective` | `string \| null` | `null` |  |
| `summary` | `string \| null` | `null` |  |
| `findings` | `array[string] \| null` | `null` |  |
| `next` | `string \| null` | `null` |  |
| `blockers` | `array[string] \| null` | `null` |  |
| `takeover` | `boolean` | `false` |  |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `plan_manage`

管理当前 logical Session 拥有的可选 Goal Plan。active Plan 会在 15 分钟无 agent 活动后启用自动续跑，最多 10 次 continuation attempt。先用 `session_manage` start/resume Session；修改类动作必须把该 Session 的 `active_run.run_id` 作为 `session_run_id`。动作：start、get、update、block、resume、finish、cancel；start 需要 objective 和 steps，finish 要求所有 step 已 completed 或 skipped。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `action` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` |  |
| `objective` | `string \| null` | `null` |  |
| `steps` | `array[object] \| null` | `null` |  |
| `step_id` | `string \| null` | `null` |  |
| `status` | `string \| null` | `null` |  |
| `text` | `string \| null` | `null` |  |
| `note` | `string \| null` | `null` |  |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `audit_tail`

读取最近的 local audit log entries。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `lines` | `integer` | `100` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Shell 与 jobs

### `run_shell`

在本地或 remote machine 运行一次非交互 shell command。适用于应快速完成的 build、test、package-manager、Git 与 inspection command；长时间、交互式或 streaming process 应使用 `shell_start` 或 `job_start`。可选 purpose/explanation 字段可说明执行原因。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `max_output_bytes` | `integer \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `run_python`

在本地或 remote machine 写入并运行短 Python script。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `code` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `shell_start`

在本地或 remote machine 启动 persistent interactive shell。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `command` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `shell_send`

向 persistent local/remote shell session 发送输入。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `input_text` | `string` | required |  |
| `enter` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `shell_read`

读取 persistent local/remote shell session 的最近输出。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `shell_stop`

终止 persistent local/remote shell session。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `shell_list`

列出本地或 remote machine 上的 persistent shell sessions。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `job_start`

在本地或 remote machine 启动一个被跟踪的 long-running job。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `job_list`

列出本地或 remote machine 上被跟踪的 jobs。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `include_finished` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `job_tail`

读取被跟踪的 local/remote job 的最近输出。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `job_stop`

停止被跟踪的 local/remote job。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `job_retry`

重新启动已停止或退出的被跟踪 local/remote job。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

## 文件与传输

### `file_list`

列出本地或 remote machine 上的文件与目录。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | `"."` |  |
| `recursive` | `boolean` | `false` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_tree`

返回本地或 remote machine 上紧凑的 directory tree。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `depth` | `integer` | `3` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_glob`

按 glob 在本地或 remote machine 查找 paths。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `pattern` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `max_results` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_grep`

搜索本地或 remote machine 的文件内容。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `query` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `regex` | `boolean` | `true` |  |
| `case_sensitive` | `boolean` | `true` |  |
| `max_results` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_read`

读取本地或 remote machine 上一个文件或一组文件。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string \| array[string]` | required |  |
| `start_line` | `integer \| null` | `null` |  |
| `end_line` | `integer \| null` | `null` |  |
| `binary_preview` | `string \| null` | `null` |  |
| `binary_preview_bytes` | `integer` | `256` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `image_view`

将 PNG、JPEG、GIF 或 WebP 文件作为原生 MCP image content 查看；需要视觉检查时优先于 `file_read`。Remote image 复用现有 file-transfer protocol，因此 worker 不需要额外的 image-specific RPC。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_write`

在本地或 remote machine 写入 UTF-8 text file。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | required |  |
| `content` | `string` | required |  |
| `overwrite` | `boolean` | `true` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_edit`

对一个本地或 remote file 应用一个或多个 exact-text edits。每个 edit 包含 old、new 和可选 `replace_all`；old 必须精确匹配，包括 whitespace 与 indentation。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | required |  |
| `edits` | `array[TextEdit]` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_delete`

删除本地或 remote file/directory。`recursive=false` 只能删除文件或空目录；非空目录必须使用 `recursive=true`，并应谨慎操作。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | required |  |
| `recursive` | `boolean` | `false` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `file_patch`

在本地或远程检查并应用 unified diff 或 file_patch envelope。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `patch` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `remote_transfer`

启动被跟踪的 job，在 controller 与远程机器之间复制文件或目录。远程上传使用可续传的 raw-binary chunk；使用 `job_list`、`job_tail`、`job_stop` 和 `job_retry` 管理传输。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `source_path` | `string` | required |  |
| `destination_path` | `string` | required |  |
| `source_machine` | `string \| null` | `null` |  |
| `destination_machine` | `string \| null` | `null` |  |
| `overwrite` | `boolean` | `false` |  |
| `chunk_size` | `integer \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

必须至少指定 `source_machine` 和 `destination_machine` 之一。省略的端点表示 controller workspace；源可以是文件或目录。

### `link_create`

为本地文件创建临时 browser-accessible URL。默认以 attachment 下载；需要在 browser 或 Markdown image 中直接渲染时设 `inline=true`。Link 是 public bearer URL，由 high-entropy token、TTL、可选 download-count limit 与显式 revocation 保护。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `path` | `string` | required |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `filename` | `string \| null` | `null` |  |
| `max_downloads` | `integer \| null` | `null` |  |
| `inline` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `link_list`

列出已生成的 local file download URLs。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `include_expired` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `link_revoke`

撤销已生成的 local file download URL。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `token` | `string` | required |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## 动态 MCP gateway

### `mcp_manage`

注册、列出、读取、启用、禁用、刷新、删除或更新 dynamic MCP servers 的隔离 environment/headers。`stdio` transport 使用 command/args/cwd，`streamable_http` transport 使用 url。Secret env/header values 会私密持久化且永不返回。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `action` | `string` | required |  |
| `name` | `string \| null` | `null` |  |
| `transport` | `string \| null` | `null` |  |
| `command` | `string \| null` | `null` |  |
| `args` | `array[string] \| null` | `null` |  |
| `cwd` | `string \| null` | `null` |  |
| `url` | `string \| null` | `null` |  |
| `env` | `object \| null` | `null` |  |
| `headers` | `object \| null` | `null` |  |
| `enabled` | `boolean` | `true` |  |
| `overwrite` | `boolean` | `false` |  |
| `refresh` | `boolean` | `true` |  |
| `key` | `string \| null` | `null` |  |
| `value` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_search`

搜索已启用 dynamic MCP servers 的 cached lightweight tool summaries。Dynamic tools 不进入本 server 的 `tools/list`；调用前先用返回的 `<server>:<tool>` 名称配合 `mcp_tool_inspect`。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `query` | `string` | `""` |  |
| `server` | `string \| null` | `null` |  |
| `limit` | `integer` | `20` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_inspect`

返回名为 `<server>:<tool>` 的 dynamic MCP tool 的完整 cached schema；如果 cache stale，先用 `mcp_manage` refresh server。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_call`

调用名为 `<server>:<tool>` 的 cached dynamic MCP tool。先用 `mcp_tool_search` 发现，再用 `mcp_tool_inspect` 检查 schema；external MCP connection 仅在本次调用期间打开。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `name` | `string` | required |  |
| `arguments` | `object \| null` | `null` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## 浏览器自动化

### `browser_session`

在本地或远程启动、列出、关闭或清理 persistent high-level browser sessions。`start` 可打开 URL、复用 persistent `profile_id` 或加载 `storage_state_path`；`close` 可保存 storage state。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `action` | `string` | required |  |
| `session_id` | `string \| null` | `null` |  |
| `browser` | `string` | `"chromium"` |  |
| `headless` | `boolean` | `true` |  |
| `width` | `integer` | `1440` |  |
| `height` | `integer` | `1000` |  |
| `url` | `string \| null` | `null` |  |
| `wait_until` | `string` | `"domcontentloaded"` |  |
| `profile_id` | `string \| null` | `null` |  |
| `storage_state_path` | `string \| null` | `null` |  |
| `save_storage_state_path` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `browser_snapshot`

捕获 persistent browser page：title、URL、bounded visible text、带 `e1` 等 stable short refs 的 interactive elements、最近 page/network errors，以及可选 screenshot path。Page 导航或重新 snapshot 前，可直接把 refs 作为 `browser_act` targets。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `page_id` | `string \| null` | `null` |  |
| `include_text` | `boolean` | `true` |  |
| `screenshot` | `boolean` | `true` |  |
| `full_page` | `boolean` | `false` |  |
| `max_text_chars` | `integer` | `100000` |  |
| `max_elements` | `integer` | `100` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `browser_act`

在 persistent browser session 执行 structured actions，支持 navigate、new_page、close_page、click、fill、type、select、press、check、uncheck、hover、wait、wait_for_text、wait_for_url。Target 可为 `browser_snapshot` 的 `e1` 等 ref 或 CSS selector；只有 high-level actions 不足时才用 `browser_run_script`。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `actions` | `array[object]` | required |  |
| `page_id` | `string \| null` | `null` |  |
| `timeout_ms` | `integer` | `30000` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

### `browser_run_script`

在本地或 remote machine 运行完整 Python Playwright script。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `script` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。

## 远程 worker 管理

### `remote_manage`

使用 action=invite、list、revoke 或 rename 管理 remote workers。invite 接受 name/workdir/ttl_s；revoke 需要 machine；rename 需要 machine 与 new_name。

| 参数 | 类型 | 必填/默认值 | 说明 |
|---|---|---|---|
| `action` | `string` | required |  |
| `name` | `string \| null` | `null` |  |
| `workdir` | `string \| null` | `null` |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `new_name` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | 始终提供此字段。没有活动 logical Session 时传 `null`；在 `session_manage` start/resume 后，传返回的 `active_run.run_id`，并在 MCP transport 重连期间持续复用。显式 resume/takeover 后改用新的值。 |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

指定 `machine` 时，调用还需要 `remote:use`，并通过远程 worker 协议执行。
