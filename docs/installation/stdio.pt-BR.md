<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Runtime Stdio

O modo stdio é destinado a MCP client locais que iniciam `local-shell-mcp` como child process e se comunicam por entrada/saída padrão.

Não é um deployment HTTP público. O ChatGPT web/app não consegue usá-lo diretamente porque o ChatGPT não pode iniciar um process na sua máquina.

## Quando usar stdio

Use stdio mode quando:

- Seu MCP client aceita definições de servidor baseadas em comandos.
- O client e o workspace controlado estão na mesma máquina.
- Você não precisa de OAuth, HTTPS público, reverse proxies ou tunnels.
- Você quer que o client gerencie o server lifecycle.

Não use stdio mode quando:

- O client é ChatGPT web/app.
- Vários remote clients precisam do mesmo servidor.
- Você precisa de downloads tokenizados por HTTP.
- Você precisa de rotas de entrada de remote workers servidas por HTTP.

## Comando

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Uma configuração genérica de MCP client geralmente contém:

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

Adapte o schema ao seu client. Alguns clients chamam esta seção de `servers`, `tools`, `mcpServers` ou `contextServers`.

## Diferenças de comportamento em relação ao HTTP mode

| Área | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Nenhum | `/mcp` |
| OAuth | Não necessário | Recomendado para uso público |
| Health endpoint | Nenhum | `/healthz`, `/readyz` |
| Uso público pelo ChatGPT | Não | Sim, atrás de HTTPS |
| Server lifecycle | client inicia process | Você gerencia process/runtime |

A tool surface usa, no restante, a mesma implementação server-side, sujeita à configuration e ao suporte do client.

## Notas de segurança

Stdio mode costuma executar diretamente no host como o mesmo usuário do MCP client. Use um workspace root restrito e evite acesso amplo ao filesystem. Mantenha full-container mode desativado, a menos que o próprio stdio esteja sendo executado em um container ou VM descartável.
