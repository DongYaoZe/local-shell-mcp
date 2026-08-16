<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Opciones de runtime y modelo de despliegue

`local-shell-mcp` plantea dos decisiones independientes:

1. **Runtime**: cómo se ejecuta el proceso del servidor y qué workspace controla.
2. **Client connection**: cómo llega ChatGPT u otro MCP client a ese servidor.

No trate ChatGPT como método de despliegue. ChatGPT es un client. Docker, VS Code extension, release binaries, instalaciones Python y stdio mode son opciones de runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Una configuración pública habitual es:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Una configuración con MCP client local puede ser más simple:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Matriz de elección de runtime

| Runtime | Mejor para | Límite de aislamiento | Origen de toolchain | Acceso público ChatGPT | Página |
|---|---|---|---|---|---|
| Docker Compose | La mayoría de cargas coding-agent y workspaces reproducibles | Container | La imagen del proyecto incluye toolchain amplia | Añadir proxy HTTPS o tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Despliegue público en una pila con Cloudflare Tunnel | Container | Project image | Integrado en perfil Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Iniciar/detener server desde un workspace de editor | Normalmente proceso host | Herramientas host más executable configurado | Añadir tunnel/proxy HTTPS externo para ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts o VM sin Docker | Host or VM | Herramientas host más executable configurado | Añadir proxy HTTPS o tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Uso Python-native, debugging y desarrollo | Host virtualenv or VM | Paquete Python más herramientas host | Añadir proxy HTTPS o tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP clients locales que crean procesos directamente | Client process boundary | Herramientas host más executable configurado | No usable por ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Matriz de conexión de client

| Ruta de client | Requiere HTTPS público | Usa `/mcp` | Requiere OAuth | Runtime típico |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Sí | Sí | Sí para uso público | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | No | No | No | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Normalmente no en localhost; sí entre redes | Sí | Recomendado fuera de localhost | Any HTTP runtime |
| VS Code extension helper flow | Solo si ChatGPT debe conectar | Sí al copiar URL de ChatGPT | Recomendado para ChatGPT | VS Code-launched runtime |

Consulte [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Qué controla cada runtime

Todos los runtimes inician el mismo código de servidor y exponen las mismas familias de MCP tools cuando están habilitadas:

- Shell y persistent shell sessions.
- Filesystem, search y patch tools.
- Operaciones Git.
- Browser automation mediante Playwright.
- Audit log y task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle y machine-routed tools.

La diferencia no es la API abstracta, sino el **operating environment** detrás de ella.

| Pregunta | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| ¿Dónde se ejecutan comandos? | Dentro del container | Normalmente en workspace host | En entorno de proceso host o VM |
| ¿Workspace predeterminado? | Mounted `/workspace` | Carpeta VS Code actual o path configurado | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| ¿Compilers/browsers preinstalados? | Sí, ampliamente | Solo si están instalados en host | Solo si están instalados en host |
| ¿Es fácil resetear? | Recrear container y volumen workspace | Depende del workspace | Depende del host/VM |
| ¿Adecuado para installs arbitrarios? | Sí si es desechable | Más arriesgado en host | Más arriesgado fuera de VM |

## Selección recomendada

Use **Docker Compose** primero salvo que tenga un motivo para no hacerlo. Ofrece el límite de seguridad más claro y el toolchain predeterminado más completo.

Use **VS Code extension** cuando el workflow empiece en el editor y quiera un launcher local. Sigue siendo un runtime. No hace por sí solo que el server sea accesible desde ChatGPT; añada tunnel o reverse proxy para ChatGPT web/app.

Use **standalone binary** cuando Docker no esté disponible pero una VM, container host o cuenta dedicada ya proporcione el límite.

Use **`pipx` o source install** para desarrollo y debugging de `local-shell-mcp`, o si un entorno Python es más fácil de mantener.

Use **stdio mode** solo para MCP clients locales que puedan crear el proceso servidor. No es despliegue público ni es usable directamente desde ChatGPT web/app.

## Regla del endpoint público

Para MCP clients HTTP como ChatGPT, el endpoint MCP es:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` contiene solo el origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

No añada `/mcp` a `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Páginas de runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Páginas de client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
