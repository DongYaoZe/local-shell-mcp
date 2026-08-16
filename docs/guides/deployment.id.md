<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Pilihan runtime dan model deployment

`local-shell-mcp` memiliki dua keputusan yang independen:

1. **Runtime**: bagaimana proses server berjalan dan workspace apa yang dikontrol.
2. **Client connection**: bagaimana ChatGPT atau MCP client lain mencapai server tersebut.

Jangan anggap ChatGPT sebagai metode deployment. ChatGPT adalah client. Docker, VS Code extension, release binaries, instalasi Python, dan stdio mode adalah pilihan runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Setup publik yang umum:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Setup MCP client lokal bisa lebih sederhana:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Matriks pilihan runtime

| Runtime | Paling cocok untuk | Batas isolasi | Sumber toolchain | Akses publik ChatGPT | Halaman |
|---|---|---|---|---|---|
| Docker Compose | Sebagian besar coding-agent workloads dan workspaces reproducible | Container | Project image memuat toolchain default luas | Tambahkan HTTPS proxy atau tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Deployment publik satu stack dengan Cloudflare Tunnel | Container | Project image | Terintegrasi di profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Start/stop server dari editor workspace | Biasanya host process | Host tools plus executable yang dikonfigurasi | Tambahkan HTTPS tunnel/proxy eksternal untuk ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Host atau VM tanpa Docker | Host or VM | Host tools plus executable yang dikonfigurasi | Tambahkan HTTPS proxy atau tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Penggunaan Python-native, debugging, development | Host virtualenv or VM | Python package plus host tools | Tambahkan HTTPS proxy atau tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP client lokal yang spawn process langsung | Client process boundary | Host tools plus executable yang dikonfigurasi | Tidak dapat dipakai ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Matriks koneksi client

| Client path | Butuh HTTPS publik | Pakai `/mcp` | Butuh OAuth | Runtime umum |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Ya | Ya | Ya untuk penggunaan publik | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Tidak | Tidak | Tidak | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Biasanya tidak di localhost; ya lintas jaringan | Ya | Disarankan di luar localhost | Any HTTP runtime |
| VS Code extension helper flow | Hanya jika ChatGPT harus connect | Ya saat copy URL ChatGPT | Disarankan untuk ChatGPT | VS Code-launched runtime |

Lihat [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Apa yang dikontrol tiap runtime

Setiap runtime menjalankan server code yang sama dan mengekspos family MCP tools yang sama ketika diaktifkan:

- Shell dan persistent shell sessions.
- Filesystem, search, dan patch tools.
- Git operations.
- Browser automation via Playwright.
- Audit log dan task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle dan machine-routed tools.

Perbedaannya bukan abstract API, melainkan **operating environment** di belakangnya.

| Pertanyaan | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Di mana command berjalan? | Di dalam container | Biasanya pada host workspace | Di host atau VM process environment |
| Default workspace? | Mounted `/workspace` | Folder VS Code saat ini atau path terkonfigurasi | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser sudah tersedia? | Ya, luas | Hanya jika terpasang di host | Hanya jika terpasang di host |
| Mudah di-reset? | Buat ulang container dan workspace volume | Tergantung workspace | Tergantung host/VM |
| Cocok untuk arbitrary package install? | Ya jika disposable | Lebih berisiko di host | Lebih berisiko di luar VM |

## Pilihan yang disarankan

Gunakan **Docker Compose** terlebih dahulu kecuali ada alasan lain. Ini memberi safety boundary paling jelas dan default toolchain paling lengkap.

Gunakan **VS Code extension** jika workflow dimulai dari editor dan Anda menginginkan local launcher. Ini tetap runtime. Ia tidak membuat server otomatis dapat dijangkau ChatGPT; tambahkan tunnel atau reverse proxy untuk ChatGPT web/app.

Gunakan **standalone binary** jika Docker tidak tersedia tetapi VM, container host, atau dedicated user account sudah memberi boundary.

Gunakan **`pipx` atau source install** untuk development/debugging `local-shell-mcp` atau jika Python-based environment lebih mudah dirawat.

Gunakan **stdio mode** hanya untuk MCP client lokal yang dapat spawn server process. Ini bukan public deployment dan tidak dapat dipakai langsung oleh ChatGPT web/app.

## Aturan public endpoint

Untuk HTTP MCP client seperti ChatGPT, MCP endpoint adalah:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` hanya origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Jangan tambahkan `/mcp` ke `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Halaman runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Halaman client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
