<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Python, pipx ve source runtimes

Python runtime’ları geliştirme, hata ayıklama ve Python package management’ın Docker’dan daha kolay olduğu ortamlar için kullanışlıdır. Docker ve binary runtime’larla aynı server’ı çalıştırırlar.

Bu sayfa üç ilgili durumu kapsar:

- `pipx install local-shell-mcp`: user-level executable kurulumu.
- `pip install local-shell-mcp`: mevcut virtual environment içine kurulum.
- Editable source checkout: projenin kendisini geliştirme veya hata ayıklama.

## pipx kurulumu

`pipx`, normal kullanıcılar için en temiz Python tabanlı kurulumdur; command’a kendi virtual environment’ını verirken executable’ı `PATH` üzerinde sunar.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Yerel HTTP MCP server başlatın:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Sağlığı kontrol edin:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Virtual environment kurulumu

Python environment’larını zaten kendiniz yönetiyorsanız kullanın:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Process host üzerinde kurulu araçları kullanır. Python package sizin için compiler, Git, browser system dependency veya project dependency kurmaz.

## Editable source checkout

Project geliştirme için:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Kontrolleri çalıştırın:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Tarayıcı kurulumu

Python package Playwright’a bağlıdır, ancak browser binary’lerin host üzerinde ayrıca kurulması gerekebilir:

```bash
python -m playwright install chromium
```

Bazı Linux host’ları ek browser dependency gerektirir. Docker, Playwright base image ile başladığı için bunun çoğunu önler.

## Genel HTTP MCP kullanımı

ChatGPT veya başka bir public HTTP MCP client için diğer HTTP runtime’larla aynı public-origin ve OAuth ayarlarını yapılandırın, ardından local port’u reverse proxy veya tunnel üzerinden açın.

Genel MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

## Geliştirme modları

| Mode | Command | Kullanım |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | HTTPS arkasındaki ChatGPT dahil, HTTP üzerinden tam MCP client’lar |
| REST-style HTTP | `local-shell-mcp --mode http` | Diagnostic veya compatibility endpoint’leri; ana ChatGPT yolu değil |
| stdio | `local-shell-mcp --mode stdio` | Process’i başlatan yerel MCP client’lar |

`mode=both` ayrılmıştır ve şu anda tek process mode olarak kullanılmamalıdır.

## Host-runtime güvenliği

Python kurulumları VM/container içine koymadığınız sürece host user olarak çalışır. Workspace’i dar tutun, full-container mode kapalı kalsın ve workspace’i home directory’ye yöneltmeyin.

Güvenilmeyen repository’ler, package-manager-heavy task’lar veya resetability’nin host integration’dan daha önemli olduğu workflow’lar için Docker Compose kullanın.
