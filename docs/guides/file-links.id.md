<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Tautan file

`local-shell-mcp` dapat mengekspos file dari workspace terkontrol melalui bearer URL berentropi tinggi. Ini berguna ketika AI menghasilkan laporan, arsip, PDF, screenshot, atau artifact lain yang perlu diunduh dari atau ditampilkan di chat.

## Kapan memakai tautan file

Gunakan tautan file untuk:

- PDF atau laporan yang dibuat.
- Screenshot dan browser artifact.
- Output build.
- Log yang terlalu besar untuk ditempel.
- Arsip yang disiapkan untuk inspeksi manual.

Jangan gunakan tautan file untuk secret, private key, penyimpanan credential, atau data pribadi yang tidak terkait.

## Alur umum

1. Buat atau temukan file di bawah `/workspace`.
2. Panggil `link_create` dengan TTL dan batas unduhan opsional. Set `inline=true` jika file harus dirender langsung di browser atau sebagai gambar Markdown; defaultnya `false`, yang memaksa attachment download.
3. Bagikan URL yang dikembalikan.
4. Cabut tautan ketika tidak lagi diperlukan.

## Tool terkait

| Tool | Tujuan |
|---|---|
| `link_create` | Membuat URL bertoken untuk file workspace. |
| `link_list` | Menampilkan tautan aktif. |
| `link_revoke` | Menonaktifkan tautan sebelum kedaluwarsa. |

## Kontrol

Opsi konfigurasi meliputi:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Gunakan TTL lebih pendek untuk artifact sensitif dan tetapkan maximum download count jika tautan ditujukan untuk satu penerima.

## Catatan keamanan

Tautan file adalah bearer URL. Siapa pun yang memiliki URL dapat mengunduh file hingga kedaluwarsa, mencapai download limit, atau dicabut. Perlakukan seperti secret sementara. Inline response mencakup CSP sandbox dan `X-Content-Type-Options: nosniff` sehingga format aktif tidak dapat mengakses LSM origin atau berjalan sebagai konten same-origin tanpa sandbox.
