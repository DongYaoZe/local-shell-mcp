# Référence des outils

Cette page est une vue d’ensemble localisée des outils. Les noms d’outils et de paramètres restent des identifiants de code afin de correspondre au MCP schema, au journal d’audit et aux valeurs renvoyées par le Runtime. Pour le détail complet des champs, utilisez la référence anglaise et le tools JSON exporté par le Runtime.

## Groupes d’outils

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

## Conseils d’utilisation

Vérifiez d’abord le contexte avec des outils en lecture seule, puis utilisez les outils d’écriture, shell, Git ou distants. Pour les appels plus sensibles, renseignez purpose ou explanation afin de faciliter l’audit.
