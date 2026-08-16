# Справочник инструментов

Эта страница — локализованный обзор инструментов. Имена инструментов и параметров остаются кодовыми идентификаторами, чтобы совпадать с MCP schema, журналом аудита и значениями Runtime. Полные сведения о полях смотрите в английском справочнике и в tools JSON, экспортируемом Runtime.

## Группы инструментов

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

## Рекомендации по использованию

Сначала уточняйте контекст инструментами только для чтения, затем используйте инструменты записи, shell, Git или удалённые инструменты. Для более рискованных вызовов заполняйте purpose или explanation для аудита.
