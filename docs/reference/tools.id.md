# Referensi alat

Halaman ini adalah ringkasan alat yang dilokalkan. Nama alat dan parameter tetap sebagai identifier kode agar sesuai dengan MCP schema, log audit, dan nilai balik Runtime. Untuk detail field lengkap, gunakan referensi bahasa Inggris dan tools JSON yang diekspor oleh Runtime.

## Grup alat

### Connector / discovery

`search`, `fetch`

### Environment / audit / task state

`environment_info`, `audit_tail`, `plan_manage`, `secret_scan`

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

## Saran penggunaan

Konfirmasi konteks terlebih dahulu dengan alat hanya-baca, lalu gunakan alat tulis, shell, Git, atau alat jarak jauh. Untuk panggilan yang lebih berisiko, isi purpose atau explanation agar mudah diaudit.
