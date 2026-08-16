<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Conector ChatGPT

Esta página trata o ChatGPT como conexão de client. Ela não escolhe o runtime. Antes de usá-la, execute o servidor com Docker, VS Code extension, um binary ou uma instalação Python.

`local-shell-mcp` foi projetado para o ChatGPT Developer Mode e clientes MCP completos. O endpoint MCP expõe diretamente a superfície normal de ferramentas do LSM.

## Pré-requisitos do runtime

Escolha e inicie um runtime primeiro:

| Runtime | Página |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Depois exponha esse runtime por um caminho de rede acessível ao ChatGPT. Consulte [network connectivity](../clients/connectivity.md).

## URL pública

O ChatGPT precisa alcançar o servidor por HTTPS. O endpoint MCP é:

```text
https://your-public-host.example.com/mcp
```

Garanta que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` corresponda ao public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Não inclua `/mcp` em `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Configuração OAuth

Configurações públicas recomendadas:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access tokens não expiram por padrão, pois sessões longas de código podem exceder vidas curtas de token. Revogue o acesso rotacionando o JWT secret ou refazendo o deployment com estado novo quando necessário.

## Adicionar o conector

1. Abra as configurações de connector ou Developer Mode MCP do ChatGPT.
2. Adicione um custom MCP server.
3. Informe a URL MCP: `https://your-public-host.example.com/mcp`.
4. Conclua o OAuth.
5. Aprove a superfície de ferramentas.

## Live Workspace MCP App

Clientes ChatGPT com suporte a MCP Apps podem renderizar `local-shell-mcp` como execution workspace interativo. Peça ao ChatGPT para abrir Live Workspace uma vez quando visibilidade em tempo real ou colaboração humana ajudar; depois a app se reconecta sozinha em vez de exigir chamadas repetidas de `workspace_open`.

Live Workspace é intencionalmente separado do reasoning do modelo. Ele mostra execution state observável e resources compartilhados:

- **Activity** mostra início, conclusão e falha de ferramentas MCP e ações humanas.
- **Terminal** conecta-se ao backend de shell persistente existente com output PTY ao vivo.
- **Files** navega, visualiza, edita, cria e exclui arquivos de workspace locais ou remotos.
- **Diff** mostra alterações Git staged e unstaged e pode enviar o diff atual ao ChatGPT para revisão.
- **Jobs** mostra jobs gerenciados e sessões persistentes.
- **Remotes** mostra workers e oferece ações de convite, renomear e revogar quando o suporte remoto está ativo.
- **Audit** expõe registros estruturados recentes de auditoria MCP.

Live Workspace é sempre collaborative: ChatGPT e a pessoa podem modificar o mesmo workspace ao mesmo tempo. Quando o host suporta, ele abre como janela flutuante estilo PiP e pode alternar entre fullscreen e janela. Não existe estado separado observe/takeover.

As views files, diff, audit e activity podem enviar operational context selecionado para o próximo model turn pelo bridge MCP Apps. É contexto explicitamente compartilhado; a UI não expõe nem reconstrói reasoning privado do modelo.

### Rede e segurança

A MCP App renderizada conecta diretamente do sandbox ao service origin configurado para tráfego de terminal/eventos de baixa latência. Portanto `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` deve ser o HTTPS origin alcançável pelo navegador do ChatGPT. O endpoint MCP continua `https://your-public-host.example.com/mcp`.

Ao abrir o workspace, é emitido um bearer token aleatório e de curta duração para o Live Workspace. O token aparece apenas em metadata do resultado MCP destinada ao app renderizado, não entra em structured content visível ao modelo e só é aceito pelas APIs human/live UI. A reconexão automática ao mesmo `live_id` reutiliza a credential atual para que views reconectadas não se invalidem entre si; ela também carrega o `session_id` lógico atual, permitindo recuperar a Session durável mesmo se o estado Live Workspace em memória tiver sido perdido. Uma nova chamada explícita a `workspace_open` rotaciona a credential. O app incorporado não usa cookies do navegador nem ambient credentials.

Clientes sem MCP Apps podem ignorar UI metadata. Todas as ferramentas MCP normais de dados continuam disponíveis com o mesmo comportamento.

## Primeiro prompt

```text
Use local-shell-mcp. Primeiro chame environment_get e depois liste a raiz do workspace. Não modifique arquivos ainda.
```

Isso verifica conectividade sem fazer mudanças.

## Regras operacionais recomendadas

Dê limites claros ao modelo:

- Trabalhar dentro de `/workspace`, salvo instrução explícita em contrário.
- Executar tests antes de commit.
- Usar `secret_scan` antes de push.
- Usar `link_create` apenas para arquivos seguros para compartilhar.
- Preferir persistent shell sessions para processos longos.
- Resumir todos os comandos que modificaram arquivos.

## Problemas de descoberta de ferramentas

Se o ChatGPT autentica mas não mostra as ferramentas esperadas:

- Confirme que o endpoint termina em `/mcp`.
- Verifique `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Verifique headers do reverse proxy e limites de request body.
- Inspecione `docker compose logs --tail=200 local-shell-mcp`.
- Confirme que o serviço está no modo `mcp` ou `both`.

## Notas de segurança

Deployments públicos devem manter OAuth ativado. Não exponha ferramentas MCP completas sem autenticação na Internet pública. Trate cada ferramenta aprovada como parte da autoridade efetiva do modelo conectado.
