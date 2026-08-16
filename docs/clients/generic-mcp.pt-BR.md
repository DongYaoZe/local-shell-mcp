<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client genéricos

`local-shell-mcp` pode ser usado pelo ChatGPT e por outros MCP client. O client decide se conecta por HTTP ou se inicia o servidor via stdio.

## MCP client HTTP

Use HTTP mode quando o servidor já estiver em execução:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint local:

```text
http://127.0.0.1:8765/mcp
```

Endpoint de rede:

```text
https://your-public-host.example.com/mcp
```

Use OAuth para qualquer endpoint acessível além de um localhost confiável.

## MCP client stdio

Use stdio mode quando o client iniciar o processo do servidor por conta própria:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Formato típico da configuração do client:

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

Os schemas variam entre clients. Alguns chamam esta seção de `mcpServers`; outros usam outro nome.

## Primeira verificação segura

Para um client recém-conectado, comece com:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Em seguida, execute uma tarefa limitada com regras explícitas de edição, testes e Git.
