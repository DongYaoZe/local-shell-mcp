<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Standalone binary runtime

Release binaries `local-shell-mcp` को Docker और Python environment के बिना चलाती हैं। इस runtime का उपयोग तब करें जब Docker उपलब्ध न हो या dedicated VM, container host, lab server या restricted user account पहले से safety boundary देता हो।

यह runtime choice है। ChatGPT access अलग से HTTPS `/mcp` endpoint के माध्यम से configure होता है।

## Release artifacts

GitHub Releases सामान्य platforms के लिए self-contained executables build करता है:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

हर archive में executable, README, license और छोटा quickstart file होता है।

## Install

1. GitHub Releases से अपने platform का archive download करें।
2. उसे extract करें।
3. Executable को `PATH` पर रखें या उसका absolute path लिख लें।
4. `local-shell-mcp --help` चलाकर binary start होने की पुष्टि करें।

Linux और macOS को सामान्यतः executable bit चाहिए:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

Windows users PowerShell से `local-shell-mcp.exe` चलाएँ या containing directory को `PATH` में configure करें।

## Minimal local run

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

दूसरे terminal में:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Public HTTP MCP run

ChatGPT या public HTTP MCP client के लिए ये configuration categories सेट करें:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Tools द्वारा controlled directory |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Local bind address और port |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | `/mcp` के बिना public HTTPS origin |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Public deployments में `oauth` उपयोग करें |
| OAuth PIN and JWT secret settings | Public OAuth authorization के लिए आवश्यक |

Local HTTP port को reverse proxy या tunnel से expose करें। Public endpoint:

```text
https://your-public-host.example.com/mcp
```

## YAML config

YAML config non-secret runtime defaults रख सकता है:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Run:

```bash
local-shell-mcp --config /path/to/config.yaml
```

`LOCAL_SHELL_MCP_` prefix वाले environment variables YAML values override करते हैं।

## Host toolchain responsibility

Binary Python application package करता है, हर developer tool नहीं। MCP tools host पर available programs call करते हैं।

अपनी tasks के लिए आवश्यक packages install करें:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; Linux releases में static tmux helper पहले से शामिल है |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

यदि आप यह host toolchain maintain नहीं करना चाहते तो Docker Compose उपयोग करें।

## Long-running service

Persistent public deployment के लिए binary को OS process supervisor के नीचे चलाएँ। ये practices रखें:

- Dedicated low-privilege OS account उपयोग करें।
- Dedicated workspace directory उपयोग करें।
- Sensitive values को world-readable files से बाहर रखें।
- Failure पर automatically restart करें।
- हर restart के बाद `/healthz` check करें।
- Troubleshooting के लिए logs उपलब्ध रखें।

## Updates

1. अपने platform का नया release archive download करें।
2. चाहें तो checksums verify करें।
3. Executable replace करें।
4. Process manager restart करें।
5. `/healthz` check करें।
6. काम जारी रखने से पहले client से `environment_get` चलवाएँ।

## Safety notes

Binary अपने operating-system user के privileges से चलता है। Public deployments के लिए dedicated low-privilege user, dedicated workspace और जहाँ संभव हो VM/container boundary उपयोग करें।

अपने personal host पर सीधे चल रहे binary के लिए `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` सेट न करें। यह setting disposable containers या VMs के लिए है।
