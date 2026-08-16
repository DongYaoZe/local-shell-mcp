<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Runtime Stdio

El modo stdio está destinado a MCP client locales que inician `local-shell-mcp` como child process y se comunican mediante entrada/salida estándar.

No es un deployment HTTP público. ChatGPT web/app no puede usarlo directamente porque ChatGPT no puede iniciar un process en su máquina.

## Cuándo usar stdio

Use stdio mode cuando:

- Su MCP client admite definiciones de servidor basadas en comandos.
- El client y el workspace controlado están en la misma máquina.
- No necesita OAuth, HTTPS público, reverse proxies ni tunnels.
- Quiere que el client gestione el lifecycle del servidor.

No use stdio mode cuando:

- El client es ChatGPT web/app.
- Varios remote clients necesitan el mismo servidor.
- Necesita descargas de archivos tokenizadas por HTTP.
- Necesita rutas de unión de remote workers servidas por HTTP.

## Comando

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Una configuración genérica de MCP client suele incluir:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Adapte el schema a su client. Algunos clients llaman a esta sección `servers`, `tools`, `mcpServers` o `contextServers`.

## Diferencias de comportamiento con HTTP mode

| Área | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Ninguno | `/mcp` |
| OAuth | No necesario | Recomendado para uso público |
| Health endpoint | Ninguno | `/healthz`, `/readyz` |
| Uso público desde ChatGPT | No | Sí, detrás de HTTPS |
| Server lifecycle | El client inicia el process | Usted gestiona el process/runtime |

Por lo demás, la tool surface usa la misma implementación server-side, sujeta a configuration y soporte del client.

## Notas de seguridad

Stdio mode suele ejecutarse directamente en el host con el mismo usuario que el MCP client. Use un workspace root limitado y evite acceso amplio al filesystem. Mantenga desactivado full-container mode salvo que stdio se ejecute dentro de un container o VM desechable.
