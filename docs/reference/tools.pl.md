# Dokumentacja narzędzi

Ta strona jest zlokalizowanym przeglądem narzędzi. Nazwy narzędzi i parametrów pozostają identyfikatorami kodu, aby zgadzały się z MCP schema, dziennikiem audytu i wartościami zwracanymi przez Runtime. Pełne szczegóły pól znajdują się w angielskiej dokumentacji i w tools JSON eksportowanym przez Runtime.

## Grupy narzędzi

### Connector / discovery

`search`, `fetch`

### Environment / audit / task state

`environment_info`, `audit_tail`, `session_manage`, `plan_manage`, `secret_scan`

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

## Zalecenia użycia

Najpierw potwierdź kontekst narzędziami tylko do odczytu, a potem używaj narzędzi zapisu, shell, Git lub zdalnych. Przy bardziej ryzykownych wywołaniach wypełnij purpose albo explanation, aby ułatwić audyt.
