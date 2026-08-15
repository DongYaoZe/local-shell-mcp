# مرجع الأدوات

هذه الصفحة نظرة عامة مترجمة على الأدوات. تبقى أسماء الأدوات والمعاملات كمعرّفات برمجية حتى تطابق MCP schema وسجل التدقيق وقيم Runtime المعادة. للحصول على تفاصيل الحقول الكاملة، استخدم المرجع الإنجليزي وملف tools JSON الذي يصدّره Runtime.

## مجموعات الأدوات

### Live Workspace

`workspace_open`


### Environment / audit / task state

`environment_get`, `audit_tail`, `session_manage`, `plan_manage`, `secret_scan`

### المهارات

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

## إرشادات الاستخدام

ابدأ بتأكيد السياق عبر أدوات القراءة فقط، ثم استخدم أدوات الكتابة أو shell أو Git أو الأدوات البعيدة. في الاستدعاءات الأعلى خطراً، املأ purpose أو explanation لتسهيل التدقيق.
