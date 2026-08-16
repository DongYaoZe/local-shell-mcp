<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Runtime binary mandiri

Release binary menjalankan `local-shell-mcp` tanpa Docker dan tanpa lingkungan Python. Gunakan runtime ini ketika Docker tidak tersedia atau dedicated VM, container host, lab server, atau restricted user account sudah menyediakan batas keamanan.

Ini adalah pilihan runtime. Akses ChatGPT dikonfigurasi terpisah melalui endpoint HTTPS `/mcp`.

## Artifact release

GitHub Releases membangun executable mandiri untuk platform umum:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

Setiap archive berisi executable, README, license, dan file quickstart singkat.

## Instalasi

1. Download archive untuk platform Anda dari GitHub Releases.
2. Ekstrak.
3. Letakkan executable di `PATH` atau catat absolute path-nya.
4. Jalankan `local-shell-mcp --help` untuk memastikan binary dapat dimulai.

Linux dan macOS biasanya memerlukan executable bit:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

Pengguna Windows sebaiknya menjalankan `local-shell-mcp.exe` dari PowerShell atau menambahkan directory yang berisi file tersebut ke `PATH`.

## Minimal local run

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Di terminal lain:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Public HTTP MCP run

Untuk ChatGPT atau public HTTP MCP client, konfigurasikan kategori berikut:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Directory yang dikontrol tool |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Local bind address dan port |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | Public HTTPS origin tanpa `/mcp` |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Gunakan `oauth` untuk public deployment |
| OAuth PIN and JWT secret settings | Diperlukan untuk public OAuth authorization |

Ekspos local HTTP port melalui reverse proxy atau tunnel. Public endpoint:

```text
https://your-public-host.example.com/mcp
```

## YAML config

YAML config dapat menyimpan runtime default yang bukan secret:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Jalankan:

```bash
local-shell-mcp --config /path/to/config.yaml
```

Environment variable dengan prefix `LOCAL_SHELL_MCP_` menimpa nilai YAML.

## Tanggung jawab host toolchain

Binary mengemas aplikasi Python, bukan setiap developer tool. MCP tool memanggil program yang tersedia di host.

Pasang apa yang dibutuhkan task Anda:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; release Linux sudah menyertakan static tmux helper |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

Jika Anda tidak ingin memelihara host toolchain ini, gunakan Docker Compose.

## Layanan jangka panjang

Untuk persistent public deployment, jalankan binary di bawah process supervisor sistem operasi. Pertahankan praktik berikut:

- Gunakan dedicated low-privilege OS account.
- Gunakan dedicated workspace directory.
- Simpan sensitive value di luar world-readable file.
- Restart otomatis saat gagal.
- Periksa `/healthz` setelah setiap restart.
- Pertahankan log untuk troubleshooting.

## Update

1. Download release archive baru untuk platform Anda.
2. Verify checksum jika diinginkan.
3. Ganti executable.
4. Restart process manager.
5. Periksa `/healthz`.
6. Minta client menjalankan `environment_get` sebelum melanjutkan pekerjaan.

## Catatan keamanan

Binary berjalan dengan privilege user sistem operasi. Untuk public deployment, gunakan dedicated low-privilege user, dedicated workspace, dan jika memungkinkan batas VM/container.

Jangan set `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` untuk binary yang berjalan langsung di personal host Anda. Setting ini ditujukan untuk disposable container atau VM.
