# ツールリファレンス

このページはローカライズされたツール参照の概要です。ツール名とパラメータ名は MCP schema、監査ログ、Runtime の戻り値と対応しやすいようにコード識別子のままにしています。完全なフィールド詳細は英語リファレンスと Runtime が出力する tools JSON を参照してください。

## ツール分類

### Live Workspace

`workspace_open`


### Environment / audit / task state

`environment_get`, `audit_tail`, `session_manage`, `plan_manage`, `secret_scan`

### Skills

`skill_list`, `skill_load`, `skill_read`

### Filesystem

`file_list`, `file_read`, `image_view`, `file_write`, `file_edit`, `file_delete`, `remote_transfer`, `file_tree`, `file_glob`, `file_grep`

### Shell and jobs

`run_shell`, `run_python`, `shell_start`, `shell_read`, `shell_send`, `shell_stop`, `shell_list`, `job_start`, `job_list`, `job_tail`, `job_stop`, `job_retry`

### Browser automation

`browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script`

### File links

`link_create`, `link_list`, `link_revoke`

### Remote workers

`remote_manage`; normal tools use optional `machine`, and `remote_transfer` handles transfers

## 利用上の指針

まず読み取り専用ツールで文脈を確認し、その後に書き込み、shell、Git、リモートツールを使います。リスクのある呼び出しでは監査のため purpose または explanation を入力します。
