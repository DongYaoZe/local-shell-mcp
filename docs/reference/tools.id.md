<!-- i18n-source-sha256: 9e104b7a893f61206aea6ed76b78bb04387fc5349535c46ffafd8f2e4c9ccd3e -->
# Referensi tools

Page ini dibangun dari MCP tool schemas yang sebenarnya. Jalankan `python scripts/generate-tools-reference.py` setelah mengubah public tool surface untuk memperbarui English reference.

Sebagian besar tool mengembalikan `ToolResult` terstruktur berisi `ok`, `message`, dan `data`. `workspace_open` mengembalikan state yang terlihat model untuk merender MCP App. Kebanyakan tool eksekusi dan file menerima `machine` opsional; abaikan untuk workspace controller dan isi untuk worker terhubung. Operasi Git sengaja memakai `run_shell` atau tool shell lain, bukan wrapper Git khusus.

## Panduan pemilihan

| Kebutuhan | Tools yang disarankan |
|---|---|
| Memantau atau berkolaborasi dengan eksekusi di ChatGPT | `workspace_open` |
| Menginspeksi environment | `environment_get`, `file_tree`, `file_read` |
| Menjalankan command singkat atau Git operation | `run_shell` |
| Menjalankan task interaktif atau panjang | `shell_start` or `job_start` |
| Membuat perubahan file yang presisi | `file_edit` or `file_patch` |
| Mentransfer file atau directory | `remote_transfer` |
| Menemukan external MCP capability | `mcp_tool_search`, then `mcp_tool_inspect` |
| Berinteraksi dengan page | `browser_session`, `browser_snapshot`, then `browser_act` |
| Menjalankan custom browser logic | `browser_run_script` |
| Bekerja pada remote machine | gunakan tool yang sama dengan `machine`; gunakan `remote_*` hanya untuk worker administration |

## Interactive workspace

### `workspace_open`

Membuka atau menggunakan ulang interactive Live Workspace untuk real-time human/agent collaboration. Panggil sekali untuk active task dan gunakan ulang floating workspace yang reconnect otomatis, bukan membukanya berulang kali. Gunakan saat terminal output, files/diffs, jobs, remotes, atau audit activity meningkatkan workflow secara nyata.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `cwd` | `string` | `"."` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

## Environment, Skills, dan task state

### `environment_get`

Mengembalikan version, workspace, auth, policy, dan environment information secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `skill_list`

Mencantumkan installed Agent Skills tanpa memuat instructions. MCP tool surface tetap tetap; penambahan atau penghapusan Skill directories terlihat pada call berikutnya.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_load`

Memuat installed Skill dengan exact name yang dikembalikan `skill_list`. Mengembalikan instructions lengkap `SKILL.md` dan related file paths.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `skill_read`

Membaca satu related text file dari installed Skill.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `path` | `string` | required |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `secret_scan`

Memindai local workspace text files untuk common secrets sebelum commit atau push.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `max_results` | `integer` | `200` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `session_manage`

Mengelola logical task Session durable yang independen dari machine dan cwd. Lakukan start sebelum kerja tool yang substantif, report pada checkpoint penting, dan resume dengan `session_id` untuk menyerahkan kerja ke run GPT/MCP baru. `resume(takeover=true)` selalu membuat agent run baru dan menggantikan run lama. Gunakan `active_run.run_id` yang dikembalikan sebagai `session_run_id` untuk report/finish/cancel dan tool berikutnya. Aksi: start, resume, get, report, list, finish, cancel, delete.

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

Mengelola Goal Plan opsional milik logical Session saat ini. Plan aktif mengaktifkan continuation otomatis setelah 15 menit tanpa aktivitas agent, dibatasi 10 percobaan. Start/resume Session lebih dulu dengan `session_manage`; action yang mengubah state harus memakai `active_run.run_id` Session sebagai `session_run_id`. Aksi: start, get, update, block, resume, finish, cancel. start memerlukan objective dan steps; finish mensyaratkan semua step completed atau skipped.

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

Membaca recent local audit log entries.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `lines` | `integer` | `100` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Shells dan jobs

### `run_shell`

Menjalankan satu non-interactive shell command secara lokal atau pada remote machine. Gunakan untuk build, test, package-manager, Git, dan inspection commands yang harus selesai segera. Untuk process long-running, interactive, atau streaming gunakan `shell_start` atau `job_start`. Optional purpose/explanation fields dapat menjelaskan alasan command dijalankan.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `max_output_bytes` | `integer \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `run_python`

Menulis dan menjalankan short Python script secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `code` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `shell_start`

Memulai persistent interactive shell secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `command` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `shell_send`

Mengirim input ke persistent local/remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `input_text` | `string` | required |  |
| `enter` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `shell_read`

Membaca recent output dari persistent local/remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `shell_stop`

Menghentikan persistent local/remote shell session.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `shell_list`

Mencantumkan persistent shell sessions secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `job_start`

Memulai tracked long-running job secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `command` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `name` | `string \| null` | `null` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `job_list`

Mencantumkan tracked jobs secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `include_finished` | `boolean` | `true` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `job_tail`

Membaca recent output dari tracked local/remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `lines` | `integer` | `200` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `job_stop`

Menghentikan tracked local/remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `job_retry`

Memulai ulang stopped/exited tracked local/remote job.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `job_id` | `string` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

## Files dan transfer

### `file_list`

Mencantumkan files dan directories secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | `"."` |  |
| `recursive` | `boolean` | `false` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_tree`

Mengembalikan compact directory tree secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `cwd` | `string` | `"."` |  |
| `depth` | `integer` | `3` |  |
| `max_entries` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_glob`

Mencari paths berdasarkan glob secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `pattern` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `max_results` | `integer` | `500` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_grep`

Mencari isi files secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `query` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `glob` | `string \| null` | `null` |  |
| `regex` | `boolean` | `true` |  |
| `case_sensitive` | `boolean` | `true` |  |
| `max_results` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_read`

Membaca satu file atau list files secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string \| array[string]` | required |  |
| `start_line` | `integer \| null` | `null` |  |
| `end_line` | `integer \| null` | `null` |  |
| `binary_preview` | `string \| null` | `null` |  |
| `binary_preview_bytes` | `integer` | `256` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `image_view`

Menampilkan PNG, JPEG, GIF, atau WebP sebagai native MCP image content secara lokal atau pada remote machine. Gunakan alih-alih `file_read` saat visual inspection diperlukan. Remote images menggunakan kembali file-transfer protocol yang ada, sehingga worker tidak memerlukan image-specific RPC.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_write`

Menulis UTF-8 text file secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `content` | `string` | required |  |
| `overwrite` | `boolean` | `true` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_edit`

Menerapkan satu atau lebih exact-text edits pada local/remote file. Setiap edit berisi old, new, dan optional `replace_all`; old harus exact match termasuk whitespace dan indentation.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `edits` | `array[TextEdit]` | required |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_delete`

Menghapus local/remote file atau directory. `recursive=false` menghapus files atau empty directories; non-empty directories memerlukan `recursive=true` dan harus digunakan dengan hati-hati.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `recursive` | `boolean` | `false` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `file_patch`

Memeriksa dan menerapkan unified diff atau file_patch envelope secara lokal atau remote.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `patch` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `purpose` | `string \| null` | `null` |  |
| `explanation` | `string \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `remote_transfer`

Memulai job terlacak yang menyalin file atau directory antara controller dan remote machine. Remote upload memakai chunk raw-binary resumable; kelola transfer dengan `job_list`, `job_tail`, `job_stop`, dan `job_retry`.

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
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Setidaknya satu dari `source_machine` dan `destination_machine` harus diberikan. Endpoint yang dihilangkan berarti workspace controller; source dapat berupa file atau directory.

### `link_create`

Membuat temporary browser-accessible URL untuk local file. Default response adalah attachment download; set `inline=true` untuk render langsung di browser atau Markdown image. Links adalah public bearer URLs yang dilindungi high-entropy token, TTL, optional download-count limit, dan explicit revocation.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `path` | `string` | required |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `filename` | `string \| null` | `null` |  |
| `max_downloads` | `integer \| null` | `null` |  |
| `inline` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `link_list`

Mencantumkan generated local file download URLs.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `include_expired` | `boolean` | `false` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `link_revoke`

Mencabut generated local file download URL.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `token` | `string` | required |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Dynamic MCP gateway

### `mcp_manage`

Mendaftarkan, mencantumkan, mengambil, mengaktifkan, menonaktifkan, refresh, menghapus, atau memperbarui isolated environment/headers dari dynamic MCP servers. Gunakan transport `stdio` dengan command/args/cwd atau `streamable_http` dengan url. Secret env/header values dipersist secara privat dan tidak pernah dikembalikan.

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
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_search`

Mencari cached lightweight tool summaries dari enabled dynamic MCP servers. Dynamic tools tetap di luar `tools/list` server ini; gunakan returned `<server>:<tool>` name dengan `mcp_tool_inspect` sebelum call.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `query` | `string` | `""` |  |
| `server` | `string \| null` | `null` |  |
| `limit` | `integer` | `20` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_inspect`

Mengembalikan full cached schema dari dynamic MCP tool bernama `<server>:<tool>`. Refresh server dengan `mcp_manage` jika cache stale.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

### `mcp_tool_call`

Memanggil cached dynamic MCP tool bernama `<server>:<tool>`. Discover dengan `mcp_tool_search` dan inspect schema dengan `mcp_tool_inspect` terlebih dahulu. External MCP connections hanya dibuka selama call ini.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `name` | `string` | required |  |
| `arguments` | `object \| null` | `null` |  |
| `timeout_s` | `integer \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

## Browser automation

### `browser_session`

Memulai, mencantumkan, menutup, atau membersihkan persistent high-level browser sessions secara lokal atau remote. `start` dapat membuka URL, reuse persistent `profile_id`, atau load `storage_state_path`; `close` dapat save storage state.

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
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `browser_snapshot`

Capture persistent browser page: title, URL, bounded visible text, interactive elements dengan stable short refs seperti `e1`, recent page/network errors, dan optional screenshot path. Gunakan refs langsung sebagai `browser_act` targets sampai page navigate atau snapshot baru diambil.

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
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `browser_act`

Menjalankan structured actions dalam persistent browser session. Mendukung navigate, new_page, close_page, click, fill, type, select, press, check, uncheck, hover, wait, wait_for_text, dan wait_for_url. `target` dapat berupa `browser_snapshot` ref seperti `e1` atau CSS selector. Gunakan `browser_run_script` hanya jika high-level actions tidak cukup.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `session_id` | `string` | required |  |
| `actions` | `array[object]` | required |  |
| `page_id` | `string \| null` | `null` |  |
| `timeout_ms` | `integer` | `30000` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

### `browser_run_script`

Menjalankan full Python Playwright script secara lokal atau pada remote machine.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `script` | `string` | required |  |
| `cwd` | `string` | `"."` |  |
| `timeout_s` | `integer` | `60` |  |
| `machine` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.

## Remote worker administration

### `remote_manage`

Mengelola remote workers dengan action=invite, list, revoke, atau rename. invite menerima name/workdir/ttl_s; revoke memerlukan machine; rename memerlukan machine dan new_name.

| Parameter | Type | Required/default | Description |
|---|---|---|---|
| `action` | `string` | required |  |
| `name` | `string \| null` | `null` |  |
| `workdir` | `string \| null` | `null` |  |
| `ttl_s` | `integer \| null` | `null` |  |
| `machine` | `string \| null` | `null` |  |
| `new_name` | `string \| null` | `null` |  |
| `session_run_id` | `string \| null` | required | Selalu berikan field ini. Gunakan `null` saat tidak ada logical Session aktif; setelah start/resume `session_manage`, berikan `active_run.run_id` yang dikembalikan dan terus gunakan selama reconnect transport MCP. Setelah resume/takeover eksplisit, gunakan nilai baru. |

OAuth scopes: `shell:read, shell:write, shell:execute, browser:use, file:share, remote:use`.

Saat `machine` diberikan, call juga memerlukan `remote:use` dan dijalankan melalui protokol remote worker.
