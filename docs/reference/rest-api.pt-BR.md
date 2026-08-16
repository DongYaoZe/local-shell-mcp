<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# API REST

A interface principal é MCP em `/mcp`. Uma superfície REST também está disponível para health checks, file links e operações de serviço selecionadas.

## Integridade

```http
GET /healthz
```

Retorna a integridade do servidor e seu estado básico.

## MCP

```http
POST /mcp
```

Endpoint MCP Streamable HTTP usado pelo ChatGPT e por outros MCP client.

## Chamadas de ferramentas via REST

As chamadas REST de ferramentas usam envelopes consistentes de sucesso/erro. Erros de validação retornam payloads estruturados com `ok: false` em vez de exceções brutas do framework.

## Agent Skills

O registro fixo de Skills também está disponível via REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Alterações nos diretórios de Skill ficam visíveis na chamada seguinte e não mudam a lista de ferramentas MCP.

## Links de arquivos

Downloads tokenizados de arquivos são servidos pelo aplicativo HTTP integrado. Os links são bearer URL com TTL, limite máximo opcional de downloads e suporte a revogação.

## Autenticação

Implantações públicas devem usar OAuth. O bypass de localhost pode ser ativado para desenvolvimento, mas acesso público sem autenticação é inseguro.
