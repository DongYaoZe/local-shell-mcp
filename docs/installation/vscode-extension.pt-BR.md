<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime da extensão VS Code

A extensão VS Code é launcher e UI de conveniência para o mesmo servidor `local-shell-mcp`. É uma escolha de runtime porque inicia o processo do servidor para o workspace atual do editor.

Ela não é o conector ChatGPT. Ao usar web/app, o ChatGPT ainda se conecta a um endpoint HTTPS público `/mcp`.

## O que a extensão faz

A extensão:

- Inicia `local-shell-mcp` para o workspace atual do VS Code.
- Para e reinicia o servidor.
- Mostra output do servidor em canal de saída do VS Code.
- Verifica `/healthz`.
- Copia a URL MCP.
- Copia prompt de setup do ChatGPT com workspace e endpoint.

A extensão não inclui o binary do servidor. Instale `local-shell-mcp` separadamente e aponte a extensão para esse executable se ele não estiver em `PATH`.

## Quando usar

Use este runtime quando:

- Normalmente começa por uma pasta do VS Code.
- Quer fluxo de botão/command palette em vez de lançar command no terminal manualmente.
- O projeto já tem dependências instaladas no host.
- Trabalha em repositories confiáveis ou workspace estreito.
- Aceita expor somente esse workspace ao modelo.

Use Docker quando:

- O repository não é confiável.
- O task instalará packages arbitrários.
- O task precisa de toolchain preinstalada ampla.
- Quer reset fácil recriando container.
- Quer boundary mais limpa que a conta host.

## Instalar o executable

Escolha um método de instalação do server:

```bash
pipx install local-shell-mcp
```

ou baixe o release binary para seu OS e coloque no `PATH`.

Depois instale o asset VSIX do release:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Alternativamente, use **Extensions: Install from VSIX...** na command palette.

## Configurações da extensão

| Setting | Finalidade | Valor típico |
|---|---|---|
| `local-shell-mcp.executablePath` | Path do server executable | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Bind address do local server | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace exposto ao MCP | Vazio para primeira pasta VS Code ou path explícito |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin copiado para prompts e URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN para OAuth authorization | Strong random value para uso público |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Mantenha `false` para direct host usage |
| `local-shell-mcp.extraEnv` | Extra environment do server process | Somente project-specific safe values |

## Fluxo básico

1. Abra uma pasta de projeto no VS Code.
2. Execute **local-shell-mcp: Start Server**.
3. Execute **Show Server Status** ou **Check Health** se disponível.
4. Use **Copy MCP URL** para client local ou **Copy ChatGPT Setup Prompt** para ChatGPT.
5. Adicione o endpoint ao client.

O local endpoint costuma ser:

```text
http://127.0.0.1:8765/mcp
```

É útil para clients locais, mas não acessível pelo ChatGPT web/app.

## Usando com ChatGPT

Para usar server iniciado pelo VS Code com ChatGPT, coloque HTTPS tunnel ou reverse proxy na frente da porta local.

Exemplo:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Defina:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

A URL copiada para ChatGPT deve terminar em `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Segurança do host runtime

A extensão geralmente executa commands como seu host user. Isso é materialmente diferente de um disposable Docker container.

Regras recomendadas:

- Abra somente o repository que quer que o model controle.
- Mantenha `allowFullContainer` desativado.
- Não defina workspace root como home directory.
- Não mantenha unrelated secrets no workspace.
- Use `secret_scan` antes de commits e pushes.
- Prefira Docker para unfamiliar repositories ou package-install-heavy tasks.

## Prompt comum

Depois de copiar setup prompt, comece com task read-only:

```text
Use local-shell-mcp. Primeiro chame environment_get e file_tree no workspace. Não modifique arquivos ainda.
```

Depois passe a bounded edit:

```text
Corrija o failing test neste workspace. Leia primeiro relevant files, faça o menor patch, execute targeted test e mostre git diff. Não faça commit até eu aprovar.
```

## Solução de problemas

| Sintoma | Verificar |
|---|---|
| Extensão não consegue iniciar server | Confirme que `local-shell-mcp.executablePath` existe e executa `--help` no terminal |
| ChatGPT não consegue alcançar | Local `127.0.0.1` URL não é pública; configure tunnel/proxy e `publicBaseUrl` |
| Tools expõem pasta errada | Defina `local-shell-mcp.workspaceRoot` explicitamente |
| Auth falha após restart | Defina OAuth admin PIN e JWT secret estáveis via `extraEnv` ou runtime configuration |
| Commands não encontram dependencies | Instale dependencies no host ou mude para Docker runtime |
