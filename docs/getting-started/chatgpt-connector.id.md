<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Konektor ChatGPT

Halaman ini membahas ChatGPT sebagai koneksi client. Halaman ini tidak memilih runtime. Sebelum menggunakannya, jalankan server dengan Docker, VS Code extension, binary, atau instalasi Python.

`local-shell-mcp` dirancang untuk ChatGPT Developer Mode dan client MCP lengkap. MCP endpoint mengekspos tool surface LSM normal secara langsung.

## Prasyarat runtime

Pilih dan jalankan satu runtime terlebih dahulu:

| Runtime | Halaman |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Lalu ekspos runtime tersebut melalui jalur jaringan yang dapat dijangkau ChatGPT. Lihat [network connectivity](../clients/connectivity.md).

## URL publik

ChatGPT harus mencapai server lewat HTTPS. MCP endpoint adalah:

```text
https://your-public-host.example.com/mcp
```

Pastikan `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` sesuai dengan public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Jangan sertakan `/mcp` dalam `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Konfigurasi OAuth

Pengaturan publik yang disarankan:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access token tidak kedaluwarsa secara default karena sesi coding panjang dapat melebihi lifetime token pendek. Cabut akses dengan merotasi JWT secret atau redeploy dengan state baru bila diperlukan.

## Menambahkan konektor

1. Buka pengaturan connector atau Developer Mode MCP ChatGPT.
2. Tambahkan custom MCP server.
3. Masukkan URL MCP: `https://your-public-host.example.com/mcp`.
4. Selesaikan OAuth.
5. Setujui permukaan tools.

## Live Workspace MCP App

Client ChatGPT dengan dukungan MCP Apps dapat merender `local-shell-mcp` sebagai execution workspace interaktif. Minta ChatGPT membuka Live Workspace sekali ketika visibilitas real-time atau kolaborasi manusia berguna; setelah itu app melakukan reconnect sendiri tanpa panggilan `workspace_open` berulang.

Live Workspace sengaja dipisahkan dari reasoning model. Ia menunjukkan execution state yang dapat diamati dan resources bersama:

- **Activity** menampilkan mulai, selesai, gagal dari MCP tools dan tindakan manusia.
- **Terminal** terhubung ke backend persistent shell yang ada dengan live PTY output.
- **Files** menjelajah, preview, edit, create, dan delete file workspace lokal atau remote.
- **Diff** menampilkan perubahan Git staged dan unstaged dan dapat mengirim current diff kembali ke ChatGPT untuk review.
- **Jobs** menampilkan managed jobs dan persistent sessions.
- **Remotes** menampilkan workers dan menyediakan tindakan invite, rename, revoke saat remote support aktif.
- **Audit** menampilkan structured MCP audit records terbaru.

Live Workspace selalu collaborative: ChatGPT dan manusia dapat mengubah workspace yang sama secara bersamaan. Ia terbuka sebagai floating PiP-style window jika host mendukung dan dapat berganti antara fullscreen dan windowed. Tidak ada state observe/takeover terpisah.

View files, diff, audit, dan activity dapat mengirim operational context terpilih ke model turn berikutnya melalui MCP Apps bridge. Ini adalah context yang dibagikan secara eksplisit; UI tidak mengekspos atau merekonstruksi private model reasoning.

### Jaringan dan keamanan

MCP App yang dirender terhubung langsung dari sandbox ke service origin yang dikonfigurasi untuk terminal/event traffic berlatensi rendah. Karena itu `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` harus berupa HTTPS origin yang dapat dijangkau browser ChatGPT. MCP endpoint tetap `https://your-public-host.example.com/mcp`.

Saat workspace dibuka, Live Workspace mengeluarkan bearer token acak berumur pendek. Token hanya dikembalikan dalam metadata hasil MCP untuk app yang dirender, tidak masuk ke structured content yang terlihat model, dan hanya diterima oleh API human/live UI. Reattachment otomatis ke `live_id` yang sama menggunakan kembali credential saat ini agar view yang reconnect tidak saling menginvalidasi; ia juga membawa logical `session_id` saat ini sehingga view dapat memulihkan Session durable walaupun state Live Workspace in-memory hilang. Panggilan `workspace_open` baru yang eksplisit merotasi credential. App tertanam tidak memakai browser cookie atau ambient credential.

Client yang tidak menerapkan MCP Apps dapat mengabaikan UI metadata. Semua MCP data tools normal tetap tersedia dan berperilaku sama.

## Prompt pertama

```text
Gunakan local-shell-mcp. Pertama panggil environment_get, lalu daftar root workspace. Jangan ubah file dulu.
```

Ini memverifikasi connectivity tanpa perubahan.

## Aturan operasi yang disarankan

Berikan constraints yang jelas kepada model:

- Bekerja di dalam `/workspace` kecuali diarahkan secara eksplisit.
- Jalankan tests sebelum commit.
- Gunakan `secret_scan` sebelum push.
- Gunakan `link_create` hanya untuk file yang aman dibagikan.
- Utamakan persistent shell sessions untuk proses panjang.
- Rangkum semua command yang mengubah file.

## Masalah tool discovery

Jika ChatGPT dapat autentikasi tetapi tools yang diharapkan tidak terlihat:

- Pastikan endpoint berakhir dengan `/mcp`.
- Periksa `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Periksa reverse proxy headers dan request body limits.
- Periksa `docker compose logs --tail=200 local-shell-mcp`.
- Pastikan service berada dalam mode `mcp` atau `both`.

## Catatan keamanan

Deployment publik harus menjaga OAuth aktif. Jangan ekspos MCP tools penuh tanpa autentikasi ke Internet publik. Perlakukan setiap tool yang disetujui sebagai bagian dari otoritas efektif model yang terhubung.
