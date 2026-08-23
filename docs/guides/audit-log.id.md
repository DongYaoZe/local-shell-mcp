<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
# Log audit

`local-shell-mcp` menulis entri audit terstruktur untuk membantu merekonstruksi apa yang dilakukan client yang terhubung.

Path default:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Apa yang dicatat

Entri audit mencakup peristiwa seperti:

- Awal/akhir tool call.
- Metadata eksekusi perintah.
- Timeout dan error yang ditangani.
- Registrasi remote worker dan aktivitas job.
- Pembuatan dan pencabutan file link.
- Peristiwa terkait autentikasi jika berlaku.

Argumen sensitif disamarkan jika server dapat mengidentifikasinya.

## Membaca log

Gunakan tool MCP:

```text
audit_tail
```

Atau periksa langsung:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Penggunaan operasional

Log audit sangat berguna untuk:

- Meninjau perintah yang mengubah file.
- Memeriksa apakah remote worker digunakan.
- Men-debug kegagalan tak terduga.
- Mendeteksi paparan file link yang tidak disengaja.
- Mendukung incident response setelah kesalahan deployment publik.

## Retensi

`audit.jsonl` aktif secara default dibatasi 20 MB oleh `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Saat pemeliharaan retensi berjalan, record lama dipindahkan ke arsip Zstandard mandiri `audit-archive/*.jsonl.zst` alih-alih dibuang; audit payload besar yang dieksternalkan juga dimasukkan ke arsip sebelum dibersihkan dari hot store.

Arsip terkompresi memiliki batas terpisah `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, default 512 MB. Jika batas terlampaui, arsip tertua dihapus lebih dahulu. Setel ke `0` untuk menonaktifkan retensi terkompresi jangka panjang. Web UI, kueri Activity/Audit, dan `audit_tail` hanya membaca hot log aktif. Arsip terkompresi adalah cold storage untuk retensi atau ekspor dan tidak didekompresi otomatis oleh kueri UI biasa.

## Keterbatasan

Log audit bukan sandbox. Log membantu ketertelusuran, tetapi tidak mencegah model terhubung melakukan tindakan dalam wewenang yang telah dikonfigurasi.
