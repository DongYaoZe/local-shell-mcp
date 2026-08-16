<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime ekstensi VS Code

Ekstensi VS Code adalah launcher dan convenience UI untuk server `local-shell-mcp` yang sama. Ini pilihan runtime karena memulai server process untuk editor workspace saat ini.

Ini bukan ChatGPT connector itu sendiri. Saat dipakai dari web/app, ChatGPT tetap terhubung ke public HTTPS `/mcp` endpoint.

## Yang dilakukan ekstensi

Ekstensi:

- Memulai `local-shell-mcp` untuk VS Code workspace saat ini.
- Stop dan restart server.
- Menampilkan server output di VS Code output channel.
- Memeriksa `/healthz`.
- Menyalin MCP URL.
- Menyalin ChatGPT setup prompt yang berisi workspace dan endpoint.

Ekstensi tidak bundle server binary. Install `local-shell-mcp` secara terpisah lalu arahkan extension ke executable jika tidak ada di `PATH`.

## Kapan digunakan

Gunakan runtime ini jika:

- Anda biasanya memulai dari VS Code folder.
- Menghendaki button/command-palette flow dibanding menjalankan terminal command manual.
- Project dependencies sudah terpasang di host.
- Bekerja pada trusted repositories atau workspace sempit.
- Nyaman mengekspos hanya workspace itu ke model.

Gunakan Docker jika:

- Repository untrusted.
- Task akan install arbitrary packages.
- Perlu broad preinstalled toolchain.
- Ingin reset mudah dengan membuat ulang container.
- Ingin boundary lebih bersih daripada host account.

## Install executable

Pilih satu server install method:

```bash
pipx install local-shell-mcp
```

atau download release binary untuk OS dan letakkan di `PATH`.

Lalu install VSIX release asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Alternatifnya gunakan **Extensions: Install from VSIX...** di command palette.

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace yang diekspos ke MCP | Empty untuk VS Code folder pertama atau explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin yang disalin ke prompts dan URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN untuk OAuth authorization | Strong random value untuk penggunaan publik |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Pertahankan `false` untuk direct host usage |
| `local-shell-mcp.extraEnv` | Extra environment untuk server process | Hanya project-specific safe values |

## Basic flow

1. Buka project folder di VS Code.
2. Jalankan **local-shell-mcp: Start Server**.
3. Jalankan **Show Server Status** atau **Check Health** jika tersedia.
4. Gunakan **Copy MCP URL** untuk local MCP client atau **Copy ChatGPT Setup Prompt** untuk ChatGPT.
5. Tambahkan endpoint ke client.

Local endpoint biasanya:

```text
http://127.0.0.1:8765/mcp
```

Berguna untuk local clients tetapi tidak reachable dari ChatGPT web/app.

## Menggunakan dengan ChatGPT

Untuk menggunakan VS Code-launched server dari ChatGPT, tambahkan HTTPS tunnel atau reverse proxy di depan local port.

Contoh bentuk:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Set:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

URL yang disalin untuk ChatGPT harus berakhir `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Ekstensi biasanya menjalankan commands sebagai host user Anda. Ini berbeda secara material dari disposable Docker container.

Aturan yang disarankan:

- Buka hanya repository yang ingin model kontrol.
- Biarkan `allowFullContainer` dinonaktifkan.
- Jangan set workspace root ke home directory.
- Jangan simpan unrelated secrets di workspace.
- Gunakan `secret_scan` sebelum commit/push.
- Utamakan Docker untuk unfamiliar repositories atau package-install-heavy tasks.

## Common prompt

Setelah menyalin setup prompt, mulai dengan read-only task:

```text
Gunakan local-shell-mcp. Pertama panggil environment_get dan file_tree pada workspace. Jangan ubah file dulu.
```

Lalu lanjut ke bounded edit:

```text
Perbaiki failing test di workspace ini. Baca relevant files terlebih dahulu, buat patch terkecil, jalankan targeted test dan tampilkan git diff. Jangan commit sampai saya menyetujui.
```

## Troubleshooting

| Gejala | Periksa |
|---|---|
| Ekstensi tidak dapat memulai server | Pastikan `local-shell-mcp.executablePath` ada dan `--help` berjalan di terminal |
| ChatGPT tidak dapat menjangkaunya | Local `127.0.0.1` URL tidak public; konfigurasi tunnel/proxy dan `publicBaseUrl` |
| Tools mengekspos folder yang salah | Set `local-shell-mcp.workspaceRoot` secara explicit |
| Auth gagal setelah restart | Set OAuth admin PIN dan JWT secret stabil melalui `extraEnv` atau runtime configuration |
| Commands kekurangan dependencies | Install dependencies pada host atau pindah ke Docker runtime |
