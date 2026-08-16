<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client generik

`local-shell-mcp` dapat digunakan oleh ChatGPT maupun MCP client lain. Client menentukan apakah akan terhubung melalui HTTP atau menjalankan server melalui stdio.

## MCP client HTTP

Gunakan HTTP mode ketika server sudah berjalan:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint lokal:

```text
http://127.0.0.1:8765/mcp
```

Endpoint jaringan:

```text
https://your-public-host.example.com/mcp
```

Gunakan OAuth untuk setiap endpoint yang dapat dijangkau di luar localhost tepercaya.

## MCP client stdio

Gunakan stdio mode ketika client menjalankan proses server sendiri:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Bentuk konfigurasi client yang umum:

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

Schema client berbeda-beda. Sebagian menyebut bagian ini `mcpServers`; yang lain memakai nama berbeda.

## Pemeriksaan aman pertama

Untuk client yang baru terhubung, mulai dengan:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Kemudian jalankan tugas terbatas dengan aturan edit, test, dan Git yang eksplisit.
