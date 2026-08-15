# Araç başvurusu

Bu sayfa araçların yerelleştirilmiş özetidir. Araç ve parametre adları MCP schema, denetim günlüğü ve Runtime dönüş değerleriyle eşleşmesi için kod tanımlayıcısı olarak kalır. Alanların tam ayrıntıları için İngilizce başvuruya ve Runtime tarafından dışa aktarılan tools JSON çıktısına bakın.

## Araç grupları

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

## Kullanım önerileri

Önce salt okunur araçlarla bağlamı doğrulayın, ardından yazma, shell, Git veya uzak araçları kullanın. Daha riskli çağrılarda denetim için purpose veya explanation doldurun.
