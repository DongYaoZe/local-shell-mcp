# Tool-Referenz

Diese Seite ist eine lokalisierte Übersicht der Tools. Tool- und Parameternamen bleiben Code-Bezeichner, damit sie zum MCP schema, zum Audit-Log und zu Runtime-Rückgabewerten passen. Vollständige Felddetails stehen in der englischen Referenz und im vom Runtime exportierten tools JSON.

## Tool-Gruppen

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

## Nutzungshinweise

Bestätige den Kontext zuerst mit read-only Tools und nutze danach Schreib-, shell-, Git- oder Remote-Tools. Fülle bei riskanteren Aufrufen purpose oder explanation aus, damit der Vorgang auditierbar bleibt.
