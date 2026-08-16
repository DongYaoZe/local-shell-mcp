<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Runtime binario independiente

Los release binaries ejecutan `local-shell-mcp` sin Docker ni entorno Python. Use este runtime cuando Docker no esté disponible o cuando una VM dedicada, un container host, un servidor de laboratorio o una cuenta de usuario restringida ya proporcione el límite de seguridad.

Esta es una elección de runtime. El acceso de ChatGPT se configura por separado mediante un endpoint HTTPS `/mcp`.

## Artifacts de release

GitHub Releases genera executables autocontenidos para plataformas comunes:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

Cada archive contiene el executable, README, license y un breve archivo quickstart.

## Instalación

1. Descargue de GitHub Releases el archive para su plataforma.
2. Extráigalo.
3. Coloque el executable en `PATH` o anote su ruta absoluta.
4. Ejecute `local-shell-mcp --help` para verificar que el binary inicia.

Linux y macOS suelen requerir el executable bit:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

En Windows, ejecute `local-shell-mcp.exe` desde PowerShell o añada su directorio a `PATH`.

## Ejecución local mínima

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

En otro terminal:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Ejecución pública HTTP MCP

Para ChatGPT o un public HTTP MCP client, configure estas categorías:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Directorio controlado por las herramientas |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Dirección bind y puerto locales |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | Public HTTPS origin, sin `/mcp` |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Use `oauth` en deployments públicos |
| OAuth PIN and JWT secret settings | Necesarios para la autorización OAuth pública |

Exponga el puerto HTTP local mediante reverse proxy o tunnel. El endpoint público es:

```text
https://your-public-host.example.com/mcp
```

## Configuración YAML

Un YAML config puede contener valores runtime no secretos:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Ejecute:

```bash
local-shell-mcp --config /path/to/config.yaml
```

Las environment variables con prefijo `LOCAL_SHELL_MCP_` sobrescriben los valores YAML.

## Responsabilidad del toolchain del host

El binary empaqueta la aplicación Python, no todas las herramientas de desarrollo. Las herramientas MCP llaman a programas disponibles en el host.

Instale lo que requieran sus tareas:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; las releases Linux ya incluyen un static tmux helper |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

Si no quiere mantener este host toolchain, use Docker Compose.

## Servicio de larga duración

Para un deployment público persistente, ejecute el binary bajo el process supervisor de su sistema operativo. Mantenga estas prácticas:

- Use una cuenta de OS dedicada y de pocos privilegios.
- Use un workspace directory dedicado.
- Guarde valores sensibles fuera de archivos world-readable.
- Reinicie automáticamente ante fallos.
- Compruebe `/healthz` después de cada reinicio.
- Mantenga logs para troubleshooting.

## Actualizaciones

1. Descargue el nuevo release archive para su plataforma.
2. Verifique checksums si lo desea.
3. Sustituya el executable.
4. Reinicie el process manager.
5. Compruebe `/healthz`.
6. Pida al client que ejecute `environment_get` antes de continuar.

## Notas de seguridad

El binary se ejecuta con los privilegios de su usuario del sistema operativo. En deployments públicos use un usuario dedicado de pocos privilegios, un workspace dedicado y, cuando sea posible, un límite VM/container.

No defina `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` para un binary ejecutado directamente en su host personal. Esa opción está pensada para containers o VM desechables.
