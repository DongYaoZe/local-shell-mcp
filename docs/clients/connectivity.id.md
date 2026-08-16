<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Konektivitas jaringan

MCP client HTTP di luar mesin memerlukan HTTPS origin yang dapat dijangkau. Halaman ini membahas routing jaringan, bukan pemilihan runtime.

client endpoint biasanya berakhir dengan `/mcp`:

```text
https://your-public-host.example.com/mcp
```

Pengaturan public base URL server hanya berisi origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Jangan sertakan `/mcp` dalam base URL tersebut.

## Opsi konektivitas

| Opsi | Kapan digunakan |
|---|---|
| Compose tunnel sidecar | Docker Compose dengan profile `tunnel` bawaan |
| Tunnel eksternal | Runtime apa pun yang harus dapat diakses dari luar jaringan lokal |
| Caddy | TLS otomatis yang sederhana |
| Nginx atau Nginx Proxy Manager | Infrastruktur Nginx yang sudah ada |
| Traefik | Routing container-native yang sudah ada |

## Path

Teruskan seluruh origin ke server yang sedang berjalan. Path penting meliputi:

| Path | Tujuan |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Pemeriksaan kesehatan |
| `/.well-known/...` | Metadata discovery client |
| `/oauth/...` | Alur otorisasi client |
| `/downloads/...` | Tautan file hasil generasi opsional |
| `/join/...`, `/remote/...` | Alur remote-worker opsional |

## Perilaku proxy

Proxy harus mempertahankan path, meneruskan request body, mendukung response yang panjang, dan menghindari timeout yang terlalu singkat.

## Pemeriksaan

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Kesalahan umum

| Kesalahan | Perbaikan |
|---|---|
| Menggunakan `https://host` alih-alih `https://host/mcp` di ChatGPT | Tambahkan `/mcp` hanya pada client endpoint |
| Mengatur `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Atur hanya origin |
| Hanya merutekan `/mcp` | Rute seluruh origin agar discovery dan otorisasi juga berfungsi |
| Menjalankan host runtime dengan workspace terlalu luas | Gunakan workspace sempit atau Docker |

## Pasangan yang disarankan

| Runtime | Pola jaringan |
|---|---|
| Docker Compose di server | Reverse proxy yang sudah ada atau Compose tunnel profile |
| Docker Compose di mesin rumah | Outbound tunnel |
| VS Code extension di laptop | Tunnel sementara untuk sesi |
| Binary di VM | Reverse proxy di VM atau edge jaringan |
| Server dev Python/source | Biasanya hanya localhost |
| Stdio mode | Tidak ada jalur HTTP; gunakan MCP client lokal |
