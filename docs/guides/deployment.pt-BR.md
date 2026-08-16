<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Opções de runtime e modelo de implantação

`local-shell-mcp` tem duas decisões independentes:

1. **Runtime**: como o processo do servidor roda e qual workspace controla.
2. **Client connection**: como ChatGPT ou outro MCP client alcança esse servidor.

Não trate ChatGPT como método de deployment. ChatGPT é um client. Docker, VS Code extension, release binaries, instalações Python e stdio mode são escolhas de runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Uma configuração pública comum é:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Uma configuração de MCP client local pode ser mais simples:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Matriz de escolha de runtime

| Runtime | Melhor para | Limite de isolamento | Fonte do toolchain | Acesso público ChatGPT | Página |
|---|---|---|---|---|---|
| Docker Compose | A maioria das cargas coding-agent e workspaces reproduzíveis | Container | Project image inclui toolchain padrão ampla | Adicionar proxy HTTPS ou tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Deployment público em uma stack com Cloudflare Tunnel | Container | Project image | Integrado ao profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Iniciar/parar server de um editor workspace | Normalmente processo host | Ferramentas host mais executable configurado | Adicionar tunnel/proxy HTTPS externo para ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts ou VM sem Docker | Host or VM | Ferramentas host mais executable configurado | Adicionar proxy HTTPS ou tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Uso Python-native, debugging, development | Host virtualenv or VM | Pacote Python mais ferramentas host | Adicionar proxy HTTPS ou tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP clients locais que iniciam processos diretamente | Client process boundary | Ferramentas host mais executable configurado | Não utilizável pelo ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Matriz de conexão client

| Caminho client | Requer HTTPS público | Usa `/mcp` | Requer OAuth | Runtime típico |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Sim | Sim | Sim para uso público | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Não | Não | Não | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Normalmente não em localhost; sim entre redes | Sim | Recomendado fora de localhost | Any HTTP runtime |
| VS Code extension helper flow | Somente se ChatGPT precisar conectar | Sim ao copiar URL ChatGPT | Recomendado para ChatGPT | VS Code-launched runtime |

Consulte [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## O que cada runtime controla

Todo runtime inicia o mesmo código de servidor e expõe as mesmas famílias de MCP tools quando habilitadas:

- Shell e persistent shell sessions.
- Filesystem, search e patch tools.
- Operações Git.
- Browser automation via Playwright.
- Audit log e task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle e machine-routed tools.

A diferença não é a API abstrata, mas o **operating environment** por trás dela.

| Pergunta | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Onde os comandos rodam? | Dentro do container | Normalmente no host workspace | No process environment do host ou VM |
| Default workspace? | Mounted `/workspace` | Pasta VS Code atual ou path configurado | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compilers/browsers pré-instalados? | Sim, amplamente | Somente se instalados no host | Somente se instalados no host |
| É fácil resetar? | Recriar container e volume workspace | Depende do workspace | Depende do host/VM |
| Adequado para installs arbitrários? | Sim, se disposable | Mais arriscado no host | Mais arriscado fora de VM |

## Seleção recomendada

Use **Docker Compose** primeiro, salvo motivo para não fazê-lo. Ele fornece o limite de segurança mais claro e o toolchain padrão mais completo.

Use **VS Code extension** quando o workflow começar no editor e você quiser um launcher local. Ainda é um runtime. Ele não torna o server acessível ao ChatGPT por si só; adicione tunnel ou reverse proxy para ChatGPT web/app.

Use **standalone binary** quando Docker não estiver disponível, mas VM, container host ou conta dedicada já fornecerem a boundary.

Use **`pipx` ou source install** para development/debugging do próprio `local-shell-mcp` ou quando um Python-based environment for mais fácil de manter.

Use **stdio mode** somente para MCP clients locais que possam spawn o server process. Não é deployment público nem utilizável diretamente pelo ChatGPT web/app.

## Regra do endpoint público

Para MCP clients HTTP como ChatGPT, o endpoint MCP é:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` é apenas o origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Não acrescente `/mcp` a `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Páginas de runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Páginas de client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
