<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
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

Arsip terkompresi memiliki batas terpisah `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, default 512 MB. Jika batas terlampaui, arsip tertua dihapus lebih dahulu. Setel ke `0` untuk menonaktifkan retensi terkompresi jangka panjang. Query terbaru hanya membaca hot log dan membuka arsip bila riwayat lama diperlukan.

## Keterbatasan

Log audit bukan sandbox. Log membantu ketertelusuran, tetapi tidak mencegah model terhubung melakukan tindakan dalam wewenang yang telah dikonfigurasi.
