<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Runtime Python, pipx, dan source

Runtime Python berguna untuk pengembangan, debugging, dan lingkungan yang lebih mudah mengelola paket Python daripada Docker. Runtime ini menjalankan server yang sama dengan runtime Docker dan binary.

Gunakan halaman ini untuk tiga kasus terkait:

- `pipx install local-shell-mcp`: instalasi executable tingkat pengguna.
- `pip install local-shell-mcp`: instalasi ke virtual environment yang sudah ada.
- Editable source checkout: mengembangkan atau men-debug project itu sendiri.

## Instalasi pipx

`pipx` adalah instalasi berbasis Python paling bersih bagi pengguna biasa karena memberikan virtual environment tersendiri untuk command sekaligus mengekspos executable di `PATH`.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Mulai server MCP HTTP lokal:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Periksa kesehatan:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Instalasi virtual environment

Gunakan jika Anda sudah mengelola lingkungan Python secara manual:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Process menggunakan tool yang terpasang di host. Paket Python tidak memasang compiler, Git, browser system dependency, atau project dependency untuk Anda.

## Editable source checkout

Gunakan untuk pengembangan project:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Jalankan pemeriksaan:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Penyiapan browser

Paket Python bergantung pada Playwright, tetapi browser binary mungkin masih perlu dipasang di host:

```bash
python -m playwright install chromium
```

Sebagian host Linux memerlukan browser dependency tambahan. Docker menghindari sebagian besar hal ini karena image dimulai dari Playwright base image.

## Penggunaan HTTP MCP publik

Untuk ChatGPT atau public HTTP MCP client lain, konfigurasikan public-origin dan OAuth yang sama dengan runtime HTTP lainnya, lalu ekspos port lokal melalui reverse proxy atau tunnel.

Endpoint MCP publik:

```text
https://your-public-host.example.com/mcp
```

## Mode pengembangan

| Mode | Command | Penggunaan |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | MCP client lengkap melalui HTTP, termasuk ChatGPT di balik HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Endpoint diagnostik atau kompatibilitas, bukan jalur utama ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | MCP client lokal yang menjalankan process |

`mode=both` dicadangkan dan saat ini tidak boleh digunakan sebagai mode satu process.

## Keamanan host runtime

Instalasi Python berjalan sebagai host user kecuali ditempatkan di VM/container. Batasi workspace, biarkan full-container mode nonaktif, dan jangan arahkan workspace ke home directory.

Gunakan Docker Compose untuk repository yang tidak dipercaya, task yang banyak memakai package manager, atau workflow ketika resetability lebih penting daripada integrasi host.
