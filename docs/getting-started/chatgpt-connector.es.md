<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Conector de ChatGPT

Esta página cubre ChatGPT como conexión de client. No elige el runtime. Antes de usarla, ejecute el servidor con Docker, VS Code extension, un binary o una instalación de Python.

`local-shell-mcp` está diseñado para ChatGPT Developer Mode y clientes MCP completos. El endpoint MCP expone directamente la superficie normal de herramientas de LSM.

## Prerrequisitos del runtime

Elija e inicie primero un runtime:

| Runtime | Página |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Después exponga ese runtime mediante una ruta de red accesible para ChatGPT. Consulte [network connectivity](../clients/connectivity.md).

## URL pública

ChatGPT debe llegar al servidor mediante HTTPS. El endpoint MCP es:

```text
https://your-public-host.example.com/mcp
```

Asegúrese de que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` coincida con el public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

No incluya `/mcp` en `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Configuración OAuth

Ajustes públicos recomendados:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Los access tokens no caducan de forma predeterminada porque las sesiones de código largas pueden superar vidas de token cortas. Revoque el acceso rotando el JWT secret o volviendo a desplegar con un estado nuevo cuando sea necesario.

## Añadir el conector

1. Abra la configuración de connector o Developer Mode MCP de ChatGPT.
2. Añada un custom MCP server.
3. Introduzca la URL MCP: `https://your-public-host.example.com/mcp`.
4. Complete OAuth.
5. Apruebe la superficie de herramientas.

## Live Workspace MCP App

Los clientes ChatGPT compatibles con MCP Apps pueden renderizar `local-shell-mcp` como un execution workspace interactivo. Pida a ChatGPT que abra Live Workspace una vez cuando ayude la visibilidad en tiempo real o la colaboración humana; después la app se reconecta sola sin llamadas repetidas a `workspace_open`.

Live Workspace está separado deliberadamente del reasoning del modelo. Muestra execution state observable y resources compartidos:

- **Activity** muestra inicios, finalizaciones y fallos de herramientas MCP, además de acciones humanas.
- **Terminal** se conecta al backend de shell persistente existente con output PTY en vivo.
- **Files** permite explorar, previsualizar, editar, crear y borrar archivos de workspace locales o remotos.
- **Diff** muestra cambios Git staged y unstaged y puede devolver el diff actual a ChatGPT para revisión.
- **Jobs** muestra jobs gestionados y sesiones persistentes.
- **Remotes** muestra workers y ofrece acciones de invitación, cambio de nombre y revocación cuando el soporte remoto está activo.
- **Audit** expone registros estructurados recientes de auditoría MCP.

Live Workspace siempre es colaborativo: ChatGPT y la persona pueden modificar simultáneamente el mismo workspace. Se abre como ventana flotante tipo PiP cuando el host lo soporta y puede alternar entre fullscreen y ventana. No existe un estado separado observe/takeover.

Las vistas de archivos, diff, audit y activity pueden enviar operational context seleccionado al siguiente turno del modelo mediante el puente MCP Apps. Es contexto compartido explícito; la UI no expone ni reconstruye reasoning privado del modelo.

### Red y seguridad

La MCP App renderizada conecta directamente desde su sandbox al service origin configurado para tráfico de terminal y eventos de baja latencia. Por tanto, `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` debe ser el HTTPS origin accesible para el navegador de ChatGPT. El endpoint MCP sigue siendo `https://your-public-host.example.com/mcp`.

Al abrir el workspace se emite un bearer token aleatorio y de corta duración para Live Workspace. El token solo aparece en metadata del resultado MCP destinada a la app renderizada, no entra en structured content visible para el modelo y solo es aceptado por las API human/live UI. La reanexión automática al mismo `live_id` reutiliza la credencial actual para que las vistas que se reconectan no se invaliden entre sí; también transporta el `session_id` lógico actual, de modo que la vista puede recuperar su Session durable aunque se haya perdido el estado Live Workspace en memoria. Una nueva llamada explícita a `workspace_open` rota la credencial. La app embebida no usa cookies del navegador ni credenciales ambientales.

Los clientes sin MCP Apps pueden ignorar la metadata UI. Todas las herramientas de datos MCP normales siguen disponibles con el mismo comportamiento.

## Primer prompt

```text
Usa local-shell-mcp. Primero llama a environment_get y después enumera la raíz del workspace. No modifiques archivos todavía.
```

Esto verifica la conectividad sin hacer cambios.

## Reglas operativas recomendadas

Dé al modelo restricciones claras:

- Trabajar dentro de `/workspace` salvo indicación explícita.
- Ejecutar tests antes de commit.
- Usar `secret_scan` antes de push.
- Usar `link_create` solo para archivos seguros para compartir.
- Preferir sesiones shell persistentes para procesos largos.
- Resumir todos los comandos que modificaron archivos.

## Problemas de descubrimiento de herramientas

Si ChatGPT se autentica pero no muestra las herramientas esperadas:

- Confirme que el endpoint termina en `/mcp`.
- Compruebe `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Compruebe headers del reverse proxy y límites de request body.
- Inspeccione `docker compose logs --tail=200 local-shell-mcp`.
- Confirme que el servicio está en modo `mcp` o `both`.

## Notas de seguridad

Los despliegues públicos deben mantener OAuth habilitado. No exponga herramientas MCP completas sin autenticación en Internet público. Trate cada herramienta aprobada como parte de la autoridad efectiva del modelo conectado.
