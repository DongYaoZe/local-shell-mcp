<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client genéricos

`local-shell-mcp` puede utilizarse desde ChatGPT y desde otros MCP client. El client decide si se conecta por HTTP o si inicia el servidor mediante stdio.

## MCP client HTTP

Use HTTP mode cuando el servidor ya esté en ejecución:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint local:

```text
http://127.0.0.1:8765/mcp
```

Endpoint de red:

```text
https://your-public-host.example.com/mcp
```

Use OAuth para cualquier endpoint accesible más allá de localhost de confianza.

## MCP client por stdio

Use stdio mode cuando el client inicie por sí mismo el proceso del servidor:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Forma típica de la configuración del client:

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

Los schemas varían entre clients. Algunos llaman a esta sección `mcpServers`; otros usan otro nombre.

## Primera comprobación segura

Para un client recién conectado, empiece con:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Después ejecute una tarea acotada con reglas explícitas de edición, pruebas y Git.
