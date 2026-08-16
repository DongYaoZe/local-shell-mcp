<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">Plano de control MCP compatible con ChatGPT</span>

# local-shell-mcp

Dé a su asistente de IA un shell controlado, un workspace real, Git, browser automation, file sharing y acceso a remote workers sin salir del chat.

<div class="hero-actions" markdown>
[Empezar](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Elegir runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Referencia de herramientas](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Entorno real de programación
Ejecute tests, inspeccione repositories, aplique patches, opere Git y mantenga audit trail desde un único MCP endpoint.
</div>

<div class="feature-card" markdown>
### Capas de runtime y client
Elija un runtime como Docker, VS Code extension, binary, Python o stdio y conecte después ChatGPT u otro MCP client por separado.
</div>

<div class="feature-card" markdown>
### Control de máquinas remotas
Conecte máquinas detrás de NAT, firewall o HPC mediante conexiones worker salientes sin abrir puertos SSH.
</div>
</div>

## Qué proporciona

`local-shell-mcp` expone un workspace local o en contenedor controlado a ChatGPT y otros clientes MCP. Proporciona shell, shell persistente, filesystem, búsqueda, patch, Git, Playwright, auditoría, Sessions lógicas durables con Plans Goal opcionales, enlaces de archivo tokenizados y herramientas de remote worker mediante un servidor MCP compatible con ChatGPT y OAuth.

Úselo cuando la IA deba inspeccionar un repository, ejecutar tests, editar archivos, operar Git, recopilar browser evidence, producir downloadable artifacts o controlar una máquina remota que solo puede conectarse de salida al control server.

## Arquitectura

```text
Capa runtime: Docker / VS Code extension / binary / Python / stdio
Capa de exposición: localhost / HTTPS proxy / tunnel / stdio pipe
Capa client: ChatGPT / generic MCP client / editor helper
Workspace controlado: /workspace or configured workspace root
Remote workers opcionales: outbound machine connections
```

El límite de aislamiento previsto es el container o VM que ejecuta el servicio.

## Empezar según el escenario

| Escenario | Empiece aquí | Por qué |
|---|---|---|
| Primer deployment público con ChatGPT | [Quickstart](getting-started/quickstart.md) | Ruta Docker Compose con OAuth y configuración `/mcp` |
| Elegir la capa runtime | [Runtime choices](guides/deployment.md) | Explica Docker, VS Code, binary, Python y stdio como opciones separadas de runtime |
| Añadir ChatGPT como client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, primer prompt seguro y tool discovery |
| Añadir LSM a DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Instalar este repository como bundle DSH manteniendo toda la superficie de herramientas LSM y remote workers |
| Ejecutar desde VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Runtime lanzado desde editor y notas de seguridad del host |
| Aprender a operar el toolset | [Usage patterns](guides/usage-patterns.md) | Plantillas de prompt y guía de elección de herramientas |
| Entender cada tool | [Tools reference](reference/tools.md) | Propósito, inputs, returns, combinaciones y notas de cada tool |
| Conectar HPC, NPU/GPU o server node | [Remote workers](guides/remote-workers.md) | Flujo de unión outbound worker y uso remoto de tools |
| Compartir archivos generados | [File links](guides/file-links.md) | URLs tokenizadas con TTL y revocación |
| Endurecer el deployment | [Security](security.md) | Aislamiento, OAuth, alcance de workspace y audit logs |

## Familias principales de tools

| Familia | Ejemplos | Uso |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts y procesos largos |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Inspección de repository y edits precisos |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Workflows de control de versiones revisables |
| Sessions y goals | `session_manage`, `plan_manage` | Handoff durable de tareas, informes de progreso y Goal mode opcional |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Interacción persistente, comprobaciones UI, screenshots, docs renderizados y texto de página |
| File links | `link_create`, `link_revoke` | Descargar artefactos generados desde chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Máquinas detrás de NAT, firewalls o flujos de login de cluster |

## Workflows típicos

### Programar con ChatGPT

1. Inicie un runtime como Docker Compose, VS Code extension, binary o Python en un workspace dedicado.
2. Exponga el runtime HTTP si ChatGPT necesita acceso de red.
3. Añada el endpoint público `/mcp` a ChatGPT.
4. Pida primero inspeccionar el repository y ejecutar checks read-only.
5. Después permita patches, tests, review de diff, commit y push cuando estén aprobados.
6. Revise audit log cuando el task implique file links o sistemas remotos.

### Host HPC o acelerador remoto

1. Cree una invitación remote worker de un solo uso.
2. Pegue el command generado en el remote host.
3. Use tools normales con `machine`; Git mediante `run_shell` y transferencias con `remote_transfer`.
4. Revoque el worker después del task.

### Generación de artefactos

1. Haga que la IA genere un file bajo `/workspace`.
2. Cree un tokenized file link con TTL/download limits.
3. Comparta el link en chat.
4. Revóquelo al terminar.

## Idioma

Este site se construye con el plugin i18n nativo de MkDocs. Use el selector de idioma de la cabecera para cambiar entre English y páginas traducidas. Las páginas sin traducción recurren a English.
