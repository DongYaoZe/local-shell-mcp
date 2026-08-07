# Référence des outils

Cette page est une vue d’ensemble localisée des outils. Les noms d’outils et de paramètres restent des identifiants de code afin de correspondre au MCP schema, au journal d’audit et aux valeurs renvoyées par le Runtime. Pour le détail complet des champs, utilisez la référence anglaise et le tools JSON exporté par le Runtime.

## Groupes d’outils

### Connector / discovery

`search`, `fetch`

### Environment / audit / task state

`environment_info`, `audit_tail`, `todo_read_tool`, `todo_write_tool`, `secret_scan`

### Skills

`skills_list`, `skill_load`, `skill_read_file`

### Filesystem

`list_files`, `read_file`, `write_file`, `edit_file`, `delete_file_or_dir`, `remote_transfer`, `tree_view`, `glob_search`, `grep_search`

### Shell and jobs

`run_shell_tool`, `run_python_tool`, `shell_start`, `shell_read`, `shell_send`, `shell_kill`, `shell_list`, `job_start`, `job_list`, `job_tail`, `job_stop`, `job_retry`

### Browser automation

`browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script`

### File links

`create_file_link`, `list_file_links`, `revoke_file_link`

### Remote workers

`remote_manage`; normal tools use optional `machine`, and `remote_transfer` handles transfers

## Conseils d’utilisation

Vérifiez d’abord le contexte avec des outils en lecture seule, puis utilisez les outils d’écriture, shell, Git ou distants. Pour les appels plus sensibles, renseignez purpose ou explanation afin de faciliter l’audit.
