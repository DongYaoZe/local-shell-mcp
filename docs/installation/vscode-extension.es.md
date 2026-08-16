<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime de extensión VS Code

La extensión de VS Code es un launcher y UI de conveniencia para el mismo servidor `local-shell-mcp`. Es una elección de runtime porque inicia el proceso servidor para el workspace actual del editor.

No es el conector de ChatGPT. ChatGPT sigue conectándose a un endpoint HTTPS público `/mcp` cuando se usa desde web/app.

## Qué hace la extensión

La extensión:

- Inicia `local-shell-mcp` para el workspace actual de VS Code.
- Detiene y reinicia el servidor.
- Muestra output del servidor en un canal de salida de VS Code.
- Comprueba `/healthz`.
- Copia la URL MCP.
- Copia un prompt de setup de ChatGPT con workspace y endpoint.

La extensión no incluye el binary del servidor. Instale `local-shell-mcp` por separado y apunte la extensión al executable si no está en `PATH`.

## Cuándo usarla

Use este runtime cuando:

- Normalmente comienza desde una carpeta de VS Code.
- Quiere flujo con botón/command palette en vez de lanzar un comando terminal manualmente.
- El proyecto ya tiene dependencias instaladas en el host.
- Trabaja con repositories de confianza o un workspace estrecho.
- Acepta exponer solo ese workspace al modelo.

Use Docker cuando:

- El repository no es de confianza.
- El task instalará paquetes arbitrarios.
- Necesita un toolchain preinstalado amplio.
- Quiere reset sencillo recreando un container.
- Quiere una boundary más limpia que su cuenta host.

## Instalar el executable

Elija un método de instalación del servidor:

```bash
pipx install local-shell-mcp
```

o descargue el release binary para su OS y póngalo en `PATH`.

Después instale el asset VSIX del release:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

También puede usar **Extensions: Install from VSIX...** en la command palette.

## Ajustes de la extensión

| Ajuste | Propósito | Valor típico |
|---|---|---|
| `local-shell-mcp.executablePath` | Path al executable del servidor | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Dirección bind del servidor local | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Puerto local del servidor | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace expuesto a MCP | Vacío para la primera carpeta VS Code o un path explícito |
| `local-shell-mcp.authMode` | Modo de autenticación | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Origin HTTPS público copiado a prompts y URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN para autorización OAuth | Valor aleatorio fuerte para uso público |
| `local-shell-mcp.allowFullContainer` | Flag de comportamiento full-container | Mantener `false` para uso directo en host |
| `local-shell-mcp.extraEnv` | Environment adicional para proceso servidor | Solo valores seguros específicos del proyecto |

## Flujo básico

1. Abra una carpeta de proyecto en VS Code.
2. Ejecute **local-shell-mcp: Start Server**.
3. Ejecute **Show Server Status** o **Check Health** si está disponible.
4. Use **Copy MCP URL** para client local o **Copy ChatGPT Setup Prompt** para ChatGPT.
5. Añada el endpoint al client.

El endpoint local suele ser:

```text
http://127.0.0.1:8765/mcp
```

Es útil para clients locales pero no accesible desde ChatGPT web/app.

## Usarlo con ChatGPT

Para usar un servidor lanzado desde VS Code con ChatGPT, añada tunnel HTTPS o reverse proxy delante del puerto local.

Forma de ejemplo:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Configure:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

La URL copiada para ChatGPT debe terminar en `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Seguridad del runtime host

La extensión suele ejecutar comandos como su usuario host. Es materialmente distinto de un container Docker desechable.

Reglas recomendadas:

- Abra solo el repository que quiere que controle el modelo.
- Mantenga `allowFullContainer` deshabilitado.
- No ponga workspace root en su home directory.
- No guarde secrets no relacionados en el workspace.
- Use `secret_scan` antes de commits y pushes.
- Prefiera Docker para repositories desconocidos o tasks con mucha instalación de paquetes.

## Prompt común

Después de copiar el prompt de setup, empiece con una tarea read-only:

```text
Usa local-shell-mcp. Primero llama a environment_get y file_tree sobre el workspace. No modifiques archivos todavía.
```

Después pase a una edición acotada:

```text
Corrige el test que falla en este workspace. Lee primero los archivos relevantes, haz el patch mínimo, ejecuta el test objetivo y muestra git diff. No hagas commit hasta que lo apruebe.
```

## Solución de problemas

| Síntoma | Comprobar |
|---|---|
| La extensión no inicia el servidor | Confirme que `local-shell-mcp.executablePath` existe y ejecuta `--help` en terminal |
| ChatGPT no puede alcanzarlo | Una URL local `127.0.0.1` no es pública; configure tunnel/proxy y `publicBaseUrl` |
| Tools exponen la carpeta incorrecta | Defina `local-shell-mcp.workspaceRoot` explícitamente |
| Auth falla tras reinicio | Defina OAuth admin PIN y JWT secret estables mediante `extraEnv` o configuración runtime |
| Los comandos no tienen dependencias | Instale dependencias en host o cambie a Docker runtime |
