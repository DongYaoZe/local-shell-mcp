# Tools reference

This page is generated from the actual MCP tool schemas. Run `python scripts/generate-tools-reference.py` after changing the public tool surface.

Most tools return a structured `ToolResult` containing `ok`, `message`, and `data`. Connector-style `search` and `fetch` use connector-compatible results, while `open_live_workspace` returns the model-visible state used to render the MCP App. Most execution and file tools accept an optional `machine`; omit it for the controller workspace and provide it for a connected worker. Git operations intentionally use `run_shell_tool` or another shell tool rather than dedicated Git wrappers.

## Selection guide

| Need | Preferred tools |
|---|---|
| Monitor or collaborate with execution in ChatGPT | `open_live_workspace` |
| Inspect an environment | `environment_info`, `tree_view`, `read_file` |
| Run a short command or Git operation | `run_shell_tool` |
| Run an interactive or long task | `shell_start` or `job_start` |
| Make exact file changes | `edit_file` or `apply_patch` |
| Transfer a file or directory | `remote_transfer` |
| Discover an external MCP capability | `mcp_tool_search`, then `mcp_tool_inspect` |
| Interact with a page | `browser_session`, `browser_snapshot`, then `browser_act` |
| Run custom browser logic | `browser_run_script` |
| Work on a remote machine | use the same tool with `machine`; use `remote_*` only for worker administration |

## Connector and discovery

### `search`

Search workspace files and return ChatGPT connector-compatible results.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `query` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `fetch`

Fetch a workspace file by id returned from search.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `id` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Interactive workspace

### `open_live_workspace`

Open or reuse the interactive Live Workspace for real-time human/agent collaboration. Call it once for an active task and reuse the self-reconnecting floating workspace instead of reopening it repeatedly. Use it when terminal output, files/diffs, jobs, remotes, or audit activity would materially improve the workflow.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `cwd` | `string` | `"."` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

## Environment, skills, and task state

### `environment_info`

Return version, workspace, auth, policy, and environment information locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `skills_list`

List installed agent skills without loading their instructions. The MCP tool surface stays fixed; adding or removing skill directories is reflected on the next call.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_load`

Load one installed agent skill by the exact name returned from skills_list. Returns SKILL.md instructions plus related file paths.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_read_file`

Read one related text file from an installed Skill.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `path` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `secret_scan`

Scan local workspace text files for common secrets before commit or push.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `max_results` | `integer` | `200` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `session_manage`

Manage a durable logical task session independent of machine and cwd. Start one before substantive tool-driven work; report semantic progress at meaningful checkpoints; resume by session_id to hand work to a new GPT/MCP run. resume with takeover=true always creates a new agent run and supersedes the old one. Use the returned active_run.run_id as session_run_id for report/finish/cancel and subsequent tools. Actions: start, resume, get, report, list, finish, cancel. start may include label/objective; report accepts summary/findings/next/blockers/objective/label.

| Parameter | Type | Required/default | Description |
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

Manage the optional Goal plan owned by the current logical session. An active plan enables automatic continuation after 15 minutes without agent activity, capped at 10 continuation attempts. Start or resume a logical session with session_manage first. Mutating actions require that session's active_run.run_id as session_run_id. Actions: start, get, update, block, resume, finish, cancel. start requires objective and steps; finish requires every step to be completed or skipped.

| Parameter | Type | Required/default | Description |
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

Read recent local audit log entries.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `lines` | `integer` | `100` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Shells and jobs

### `run_shell_tool`

Run one non-interactive shell command locally or on a remote machine. Use for build, test, package-manager, Git, and inspection commands that should finish promptly. For long-running, interactive, or streaming processes, use shell_start or job_start. Optional purpose/explanation fields let agents state why the command is being run.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `max_output_bytes` | `integer \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `run_python_tool`

Write and run a short Python script locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `code` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `shell_start`

Start a persistent interactive shell locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `command` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `shell_send`

Send input to a persistent local or remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `input_text` | `string` | required |  |
| `enter` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `shell_read`

Read recent output from a persistent local or remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `shell_kill`

Terminate a persistent local or remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `shell_list`

List persistent shell sessions locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `job_start`

Start a tracked long-running job locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `job_list`

List tracked jobs locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `include_finished` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `job_tail`

Read recent output for a tracked local or remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `job_stop`

Stop a tracked local or remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `job_retry`

Restart a stopped or exited tracked local or remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

## Files and transfer

### `list_files`

List files and directories locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | `"."` |  |
| `recursive` | `boolean` | `false` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `tree_view`

Return a compact directory tree locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `depth` | `integer` | `3` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `glob_search`

Find paths by glob locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `pattern` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `max_results` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `grep_search`

Search file contents locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `query` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `regex` | `boolean` | `true` |  |
| `case_sensitive` | `boolean` | `true` |  |
| `max_results` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `read_file`

Read one file or a list of files locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string \| array[string]` | required |  |
| `start_line` | `integer \| null` | `null` |  |
| `end_line` | `integer \| null` | `null` |  |
| `binary_preview` | `string \| null` | `null` |  |
| `binary_preview_bytes` | `integer` | `256` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `view_image`

View a PNG, JPEG, GIF, or WebP file as native MCP image content locally or on a remote machine. Use this instead of read_file when visual inspection is needed. Remote images reuse the existing file-transfer protocol, so the worker does not need a new image-specific RPC.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `write_file`

Write a UTF-8 text file locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `content` | `string` | required |  |
| `overwrite` | `boolean` | `true` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `edit_file`

Apply one or more exact-text edits to one local or remote file. Each edits entry contains old, new, and optional replace_all; old must match exactly, including whitespace and indentation.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `edits` | `array[TextEdit]` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `delete_file_or_dir`

Delete a local or remote file or directory. recursive=false deletes files or empty directories; recursive=true is required for non-empty directories and should be used carefully.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `recursive` | `boolean` | `false` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `apply_patch`

Check and apply a unified diff or an apply_patch envelope locally or remotely.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `patch` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `remote_transfer`

Start a tracked job that copies a file or directory between the controller and remote machines. Remote uploads use resumable raw-binary chunks; use job_list, job_tail, job_stop, and job_retry to manage the transfer.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `source_path` | `string` | required |  |
| `destination_path` | `string` | required |  |
| `source_machine` | `string \| null` | `null` |  |
| `destination_machine` | `string \| null` | `null` |  |
| `overwrite` | `boolean` | `false` |  |
| `chunk_size` | `integer \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

At least one of `source_machine` and `destination_machine` must be supplied. Omitted endpoints refer to the controller workspace; the source may be either a file or a directory.

### `create_file_link`

Create a temporary browser-accessible URL for a local file. By default the response is an attachment download; set inline=true when the file should render directly in a browser or Markdown image. Links are public bearer URLs protected by a high-entropy token, TTL, optional download-count limit, and explicit revocation.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `filename` | `string \| null` | `null` |  |
| `max_downloads` | `integer \| null` | `null` |  |
| `inline` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `list_file_links`

List generated local file download URLs.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `include_expired` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `revoke_file_link`

Revoke a generated local file download URL.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `token` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Dynamic MCP gateway

### `mcp_manage`

Register, list, get, enable, disable, refresh, remove, or update the isolated environment/headers of dynamic MCP servers. Use transport=stdio with command/args/cwd, or transport=streamable_http with url. Secret env/header values are persisted privately and are never returned.

| Parameter | Type | Required/default | Description |
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
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_search`

Search cached lightweight tool summaries from enabled dynamic MCP servers. Dynamic tools stay out of this server's tools/list; use the returned <server>:<tool> name with mcp_tool_inspect before calling it.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `query` | `string` | `""` |  |
| `server` | `string \| null` | `null` |  |
| `limit` | `integer` | `20` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_inspect`

Return the full cached schema for one dynamic MCP tool named <server>:<tool>. Refresh the server with mcp_manage if its cached schema is stale.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_call`

Call one cached dynamic MCP tool named <server>:<tool>. Discover it with mcp_tool_search and inspect its schema with mcp_tool_inspect first. External MCP connections are opened only for the duration of this call.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `arguments` | `object \| null` | `null` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Browser automation

### `browser_session`

Start, list, close, or clean up persistent high-level browser sessions locally or remotely. start can open a URL, reuse a persistent profile_id, or load storage_state_path; close can save storage state.

| Parameter | Type | Required/default | Description |
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
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `browser_snapshot`

Capture a persistent browser page: title, URL, bounded visible text, interactive elements with stable short refs such as e1, recent page/network errors, and an optional screenshot path. Use refs directly as browser_act targets until the page navigates or a new snapshot is taken.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `page_id` | `string \| null` | `null` |  |
| `include_text` | `boolean` | `true` |  |
| `screenshot` | `boolean` | `true` |  |
| `full_page` | `boolean` | `false` |  |
| `max_text_chars` | `integer` | `100000` |  |
| `max_elements` | `integer` | `100` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `browser_act`

Run structured actions in a persistent browser session. Supports navigate, new_page, close_page, click, fill, type, select, press, check, uncheck, hover, wait, wait_for_text, and wait_for_url. target may be a browser_snapshot ref such as e1 or a CSS selector. Use browser_run_script only when these high-level actions are insufficient.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `actions` | `array[object]` | required |  |
| `page_id` | `string \| null` | `null` |  |
| `timeout_ms` | `integer` | `30000` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

### `browser_run_script`

Run a full Python Playwright script locally or on a remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `script` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.

## Remote worker administration

### `remote_manage`

Manage remote workers with action=invite, list, revoke, or rename. invite accepts name/workdir/ttl_s; revoke requires machine; rename requires machine and new_name.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `action` | `string` | required |  |
| `name` | `string \| null` | `null` |  |
| `workdir` | `string \| null` | `null` |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `new_name` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | `null` | Run lease returned as active_run.run_id by session_manage. Required for tool calls while a logical session is attached; use the new value after resume/takeover. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

When `machine` is supplied, the call additionally requires `remote:use` and runs through the remote worker protocol.
