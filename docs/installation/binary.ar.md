<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Standalone binary runtime

تشغّل release binaries ‏`local-shell-mcp` من دون Docker ومن دون Python environment. استخدم هذا runtime عندما لا يكون Docker متاحاً أو عندما توفر dedicated VM أو container host أو lab server أو restricted user account حدود الأمان بالفعل.

هذا اختيار runtime. يتم إعداد وصول ChatGPT بشكل منفصل عبر HTTPS endpoint ‏`/mcp`.

## Release artifacts

تبني GitHub Releases ‏self-contained executables للمنصات الشائعة:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

يحتوي كل archive على executable وREADME وlicense وquickstart file مختصر.

## التثبيت

1. نزّل archive الخاص بمنصتك من GitHub Releases.
2. فكّه.
3. ضع executable على `PATH` أو سجّل absolute path له.
4. شغّل `local-shell-mcp --help` للتحقق من أن binary يبدأ.

عادة ما يحتاج Linux وmacOS إلى executable bit:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

على Windows، شغّل `local-shell-mcp.exe` من PowerShell أو أضف المجلد المحتوي عليه إلى `PATH`.

## Minimal local run

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

في terminal آخر:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Public HTTP MCP run

لـ ChatGPT أو public HTTP MCP client، اضبط فئات الإعداد التالية:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Directory تتحكم بها tools |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Local bind address وport |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | Public HTTPS origin من دون `/mcp` |
| `LOCAL_SHELL_MCP_AUTH_MODE` | استخدم `oauth` في public deployments |
| OAuth PIN and JWT secret settings | مطلوبة لـ public OAuth authorization |

اكشف local HTTP port عبر reverse proxy أو tunnel. الـ public endpoint هو:

```text
https://your-public-host.example.com/mcp
```

## YAML config

يمكن أن يحتوي YAML config على runtime defaults غير السرية:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

شغّل:

```bash
local-shell-mcp --config /path/to/config.yaml
```

تتجاوز environment variables ذات prefix ‏`LOCAL_SHELL_MCP_` قيم YAML.

## مسؤولية host toolchain

يضم binary تطبيق Python، وليس كل developer tool. تستدعي MCP tools البرامج المتاحة على host.

ثبّت ما تحتاجه مهامك:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; تتضمن Linux releases بالفعل static tmux helper |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

إذا كنت لا تريد صيانة هذا host toolchain، فاستخدم Docker Compose.

## Long-running service

لـ persistent public deployment، شغّل binary تحت process supervisor لنظام التشغيل. اتبع الممارسات التالية:

- استخدم dedicated low-privilege OS account.
- استخدم dedicated workspace directory.
- خزّن sensitive values خارج world-readable files.
- أعد التشغيل تلقائياً عند failure.
- افحص `/healthz` بعد كل restart.
- أبقِ logs متاحة لـ troubleshooting.

## Updates

1. نزّل release archive الجديد لمنصتك.
2. Verify checksums إذا رغبت.
3. استبدل executable.
4. Restart process manager.
5. افحص `/healthz`.
6. اطلب من client تشغيل `environment_get` قبل متابعة العمل.

## ملاحظات الأمان

يعمل binary بصلاحيات مستخدم نظام التشغيل. في public deployments استخدم dedicated low-privilege user وdedicated workspace وحدود VM/container حيث أمكن.

لا تضبط `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` لbinary يعمل مباشرة على personal host. هذا الإعداد مخصص لـ disposable containers أو VMs.
