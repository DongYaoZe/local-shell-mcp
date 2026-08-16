<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Bağımsız binary runtime

Release binary’leri `local-shell-mcp`’yi Docker ve Python environment olmadan çalıştırır. Docker kullanılamıyorsa veya dedicated VM, container host, lab server ya da restricted user account zaten güvenlik sınırı sağlıyorsa bu runtime’ı kullanın.

Bu bir runtime seçimidir. ChatGPT erişimi ayrıca HTTPS `/mcp` endpoint üzerinden yapılandırılır.

## Release artifacts

GitHub Releases yaygın platformlar için self-contained executables oluşturur:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

Her archive executable, README, license ve kısa quickstart file içerir.

## Kurulum

1. Platformunuz için archive’ı GitHub Releases’tan indirin.
2. Açın.
3. Executable’ı `PATH` üzerine koyun veya absolute path’ini kaydedin.
4. Binary’nin başladığını doğrulamak için `local-shell-mcp --help` çalıştırın.

Linux ve macOS genellikle executable bit gerektirir:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

Windows kullanıcıları `local-shell-mcp.exe` dosyasını PowerShell’den çalıştırmalı veya bulunduğu directory’yi `PATH` içine eklemelidir.

## Minimal local run

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Başka bir terminalde:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Public HTTP MCP run

ChatGPT veya public HTTP MCP client için şu configuration kategorilerini ayarlayın:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Tools tarafından kontrol edilen directory |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Local bind address ve port |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | `/mcp` olmadan public HTTPS origin |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Public deployment için `oauth` kullanın |
| OAuth PIN and JWT secret settings | Public OAuth authorization için gerekli |

Local HTTP port’u reverse proxy veya tunnel üzerinden açın. Public endpoint:

```text
https://your-public-host.example.com/mcp
```

## YAML config

YAML config secret olmayan runtime default’larını tutabilir:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Çalıştırın:

```bash
local-shell-mcp --config /path/to/config.yaml
```

`LOCAL_SHELL_MCP_` prefix’li environment variable’lar YAML values üzerine yazılır.

## Host toolchain sorumluluğu

Binary Python application’ı paketler, her developer tool’u değil. MCP tools host üzerinde bulunan programları çağırır.

Task’larınızın ihtiyaç duyduklarını kurun:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; Linux release’leri static tmux helper içerir |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

Bu host toolchain’i sürdürmek istemiyorsanız Docker Compose kullanın.

## Uzun süre çalışan service

Persistent public deployment için binary’yi işletim sisteminizin process supervisor’ı altında çalıştırın. Şunları uygulayın:

- Dedicated low-privilege OS account kullanın.
- Dedicated workspace directory kullanın.
- Sensitive values’ı world-readable file dışında tutun.
- Failure durumunda otomatik restart edin.
- Her restart sonrası `/healthz` kontrol edin.
- Troubleshooting için log’ları saklayın.

## Updates

1. Platformunuz için yeni release archive’ı indirin.
2. İsterseniz checksum’ları verify edin.
3. Executable’ı değiştirin.
4. Process manager’ı restart edin.
5. `/healthz` kontrol edin.
6. Çalışmaya devam etmeden önce client’tan `environment_get` çalıştırmasını isteyin.

## Güvenlik notları

Binary, işletim sistemi kullanıcısının privilege’larıyla çalışır. Public deployment için dedicated low-privilege user, dedicated workspace ve mümkünse VM/container boundary kullanın.

Personal host üzerinde doğrudan çalışan binary için `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` ayarlamayın. Bu setting disposable container veya VM’ler içindir.
