<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Mode stdio ditujukan untuk MCP client lokal yang menjalankan `local-shell-mcp` sebagai child process dan berkomunikasi melalui standard input/output.

Ini bukan deployment HTTP publik. ChatGPT web/app tidak dapat menggunakannya secara langsung karena ChatGPT tidak dapat membuat process di mesin Anda.

## Kapan memakai stdio

Gunakan stdio mode ketika:

- MCP client mendukung definisi server berbasis command.
- Client dan workspace yang dikontrol berada di mesin yang sama.
- Anda tidak memerlukan OAuth, HTTPS publik, reverse proxy, atau tunnel.
- Anda ingin client mengelola server lifecycle.

Jangan gunakan stdio mode ketika:

- Client adalah ChatGPT web/app.
- Beberapa remote client membutuhkan server yang sama.
- Anda memerlukan tokenized file download melalui HTTP.
- Anda memerlukan remote-worker join route yang dilayani lewat HTTP.

## Perintah

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Konfigurasi MCP client umum biasanya berisi:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Sesuaikan schema dengan client Anda. Sebagian client menyebut bagian ini `servers`, `tools`, `mcpServers`, atau `contextServers`.

## Perbedaan perilaku dari HTTP mode

| Area | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Tidak ada | `/mcp` |
| OAuth | Tidak diperlukan | Direkomendasikan untuk penggunaan publik |
| Health endpoint | Tidak ada | `/healthz`, `/readyz` |
| Penggunaan ChatGPT publik | Tidak | Ya, di balik HTTPS |
| Server lifecycle | client menjalankan process | Anda mengelola process/runtime |

Selain itu, tool surface menggunakan implementasi server-side yang sama, tergantung configuration dan dukungan client.

## Catatan keamanan

Stdio mode sering berjalan langsung di host sebagai user yang sama dengan MCP client. Gunakan workspace root yang sempit dan hindari akses filesystem yang luas. Biarkan full-container mode dinonaktifkan kecuali stdio sendiri berjalan di dalam container atau VM yang dapat dibuang.
