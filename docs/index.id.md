<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">Control plane MCP yang kompatibel dengan ChatGPT</span>

# local-shell-mcp

Berikan AI assistant Anda shell terkontrol, workspace nyata, Git, browser automation, file sharing, dan akses remote-worker tanpa meninggalkan chat.

<div class="hero-actions" markdown>
[Mulai](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Pilih runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Referensi tools](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Lingkungan coding nyata
Jalankan tests, inspeksi repositories, patch files, operasikan Git, dan simpan audit trail dari satu MCP endpoint.
</div>

<div class="feature-card" markdown>
### Lapisan runtime dan client
Pilih runtime seperti Docker, VS Code extension, binary, Python, atau stdio, lalu hubungkan ChatGPT atau MCP client lain secara terpisah.
</div>

<div class="feature-card" markdown>
### Kontrol remote machine
Hubungkan mesin di balik NAT, firewall, atau HPC melalui outbound worker connections tanpa membuka port SSH.
</div>
</div>

## Yang disediakan

`local-shell-mcp` mengekspos workspace local atau container yang terkontrol ke ChatGPT dan client MCP lain. Ia menyediakan shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, logical Session durable dengan Goal Plan opsional, tokenized file link, dan tool remote-worker melalui server MCP kompatibel ChatGPT dengan OAuth.

Gunakan saat AI perlu inspeksi repository, menjalankan tests, mengedit files, mengoperasikan Git, mengumpulkan browser evidence, membuat downloadable artifacts, atau mengontrol remote machine yang hanya dapat terhubung outbound ke control server.

## Arsitektur

```text
Lapisan runtime: Docker / VS Code extension / binary / Python / stdio
Lapisan exposure: localhost / HTTPS proxy / tunnel / stdio pipe
Lapisan client: ChatGPT / generic MCP client / editor helper
Workspace terkontrol: /workspace or configured workspace root
Remote workers opsional: outbound machine connections
```

Isolation boundary yang dimaksud adalah container atau VM tempat service berjalan.

## Mulai berdasarkan skenario

| Skenario | Mulai di sini | Alasan |
|---|---|---|
| Deployment ChatGPT publik pertama | [Quickstart](getting-started/quickstart.md) | Jalur Docker Compose dengan OAuth dan setup `/mcp` |
| Memilih runtime layer | [Runtime choices](guides/deployment.md) | Menjelaskan Docker, VS Code, binary, Python, dan stdio sebagai opsi runtime terpisah |
| Menambahkan ChatGPT sebagai client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, prompt aman pertama, tool discovery |
| Menambahkan LSM ke DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Instal repository ini sebagai bundle DSH sambil mempertahankan seluruh tool dan remote-worker surface LSM |
| Menjalankan dari VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Runtime yang diluncurkan editor dan catatan keamanan host |
| Belajar mengoperasikan toolset | [Usage patterns](guides/usage-patterns.md) | Template prompt dan panduan pemilihan tools |
| Memahami setiap tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations, dan notes untuk setiap tool |
| Menghubungkan HPC, NPU/GPU, atau server node | [Remote workers](guides/remote-workers.md) | Outbound worker join flow dan remote tool usage |
| Membagikan file yang dihasilkan | [File links](guides/file-links.md) | Tokenized download URL dengan TTL dan revocation |
| Mengeraskan deployment | [Security](security.md) | Isolation, OAuth, workspace scope, dan audit logs |

## Family tools utama

| Family | Contoh | Penggunaan |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection dan precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Reviewable source-control workflows |
| Sessions dan goals | `session_manage`, `plan_manage` | Durable task handoff, progress report, dan optional Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI checks, screenshots, rendered docs, dan page text |
| File links | `link_create`, `link_revoke` | Download generated artifacts dari chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Machines di balik NAT, firewalls, atau cluster login flows |

## Workflow umum

### Coding dengan ChatGPT

1. Mulai runtime seperti Docker Compose, VS Code extension, binary, atau Python dalam dedicated workspace.
2. Expose HTTP runtime jika ChatGPT memerlukan network access.
3. Tambahkan public `/mcp` endpoint ke ChatGPT.
4. Minta terlebih dahulu inspeksi repository dan read-only checks.
5. Setelah disetujui, izinkan patch files, tests, diff review, commit, dan push.
6. Review audit log saat task melibatkan file links atau remote systems.

### Remote HPC atau accelerator host

1. Buat one-time remote worker invite.
2. Tempel generated command pada remote host.
3. Gunakan normal tools dengan `machine`; Git melalui `run_shell` dan transfer melalui `remote_transfer`.
4. Revoke worker setelah task.

### Artifact generation

1. Biarkan AI generate file di bawah `/workspace`.
2. Buat tokenized file link dengan TTL/download limits.
3. Bagikan link di chat.
4. Revoke setelah selesai.

## Bahasa

Site ini dibangun dengan native MkDocs i18n plugin. Gunakan language selector di header untuk berganti antara English dan translated pages. Page tanpa translation fallback ke English.
