<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Log dibatasi oleh `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Lakukan rotasi atau ekspor secara eksternal jika membutuhkan retensi panjang.

## Keterbatasan

Log audit bukan sandbox. Log membantu ketertelusuran, tetapi tidak mencegah model terhubung melakukan tindakan dalam wewenang yang telah dikonfigurasi.
