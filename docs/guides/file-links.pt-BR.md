<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Links de arquivos

`local-shell-mcp` pode expor arquivos do workspace controlado por meio de bearer URLs de alta entropia. Isso é útil quando a IA gera relatórios, arquivos compactados, PDFs, screenshots ou outros artifacts que precisam ser baixados ou exibidos no chat.

## Quando usar links de arquivos

Use links de arquivos para:

- PDFs ou relatórios gerados.
- Screenshots e artifacts do navegador.
- Saídas de build.
- Logs grandes demais para colar.
- Arquivos preparados para inspeção manual.

Não use links de arquivos para secrets, private keys, armazenamentos de credentials ou dados pessoais não relacionados.

## Fluxo típico

1. Gere ou localize um arquivo em `/workspace`.
2. Chame `link_create` com um TTL e limite opcional de downloads. Defina `inline=true` quando o arquivo deva renderizar diretamente no navegador ou como imagem Markdown; o padrão é `false`, que força download como attachment.
3. Compartilhe a URL retornada.
4. Revogue o link quando não for mais necessário.

## Ferramentas relevantes

| Tool | Finalidade |
|---|---|
| `link_create` | Criar uma URL tokenizada para um arquivo do workspace. |
| `link_list` | Mostrar links ativos. |
| `link_revoke` | Desabilitar um link antes de expirar. |

## Controles

As opções de configuração incluem:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Use TTLs menores para artifacts sensíveis e defina maximum download count quando o link se destinar a um único destinatário.

## Notas de segurança

Links de arquivos são bearer URLs. Qualquer pessoa com a URL pode baixar o arquivo até ele expirar, atingir o download limit ou ser revogado. Trate-os como secrets temporários. Respostas inline incluem CSP sandbox e `X-Content-Type-Options: nosniff`, impedindo formatos ativos de acessar o LSM origin ou executar como conteúdo same-origin sem sandbox.
