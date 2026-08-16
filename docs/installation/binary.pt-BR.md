<!-- i18n-source-sha256: 42daa6d3dd931530a1d2e86d6a36fc6424b7494ff078626157c158b38b1f4b1e -->
# Runtime binário independente

Release binaries executam `local-shell-mcp` sem Docker e sem ambiente Python. Use este runtime quando Docker não estiver disponível ou quando uma VM dedicada, container host, servidor de laboratório ou conta de usuário restrita já fornecer a fronteira de segurança.

Esta é uma escolha de runtime. O acesso do ChatGPT é configurado separadamente por um endpoint HTTPS `/mcp`.

## Artifacts de release

GitHub Releases cria executables autocontidos para plataformas comuns:

| Platform artifact | Archive |
|---|---|
| `local-shell-mcp-linux-x86_64` | `.tar.gz` |
| `local-shell-mcp-linux-aarch64` | `.tar.gz` |
| `local-shell-mcp-macos-x86_64` | `.tar.gz` |
| `local-shell-mcp-macos-aarch64` | `.tar.gz` |
| `local-shell-mcp-windows-x86_64` | `.zip` |

Cada archive contém o executable, README, license e um arquivo quickstart curto.

## Instalação

1. Baixe do GitHub Releases o archive da sua plataforma.
2. Extraia-o.
3. Coloque o executable no `PATH` ou registre o caminho absoluto.
4. Execute `local-shell-mcp --help` para confirmar que o binary inicia.

Linux e macOS normalmente exigem o executable bit:

```bash
chmod +x local-shell-mcp
./local-shell-mcp --help
```

No Windows, execute `local-shell-mcp.exe` pelo PowerShell ou adicione o diretório que o contém ao `PATH`.

## Execução local mínima

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Em outro terminal:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Execução pública HTTP MCP

Para ChatGPT ou um public HTTP MCP client, configure estas categorias:

| Setting | Purpose |
|---|---|
| `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | Diretório controlado pelas ferramentas |
| `LOCAL_SHELL_MCP_HOST` and `LOCAL_SHELL_MCP_PORT` | Endereço bind e porta locais |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | Public HTTPS origin sem `/mcp` |
| `LOCAL_SHELL_MCP_AUTH_MODE` | Use `oauth` em deployments públicos |
| OAuth PIN and JWT secret settings | Necessários para autorização OAuth pública |

Exponha a porta HTTP local por reverse proxy ou tunnel. O endpoint público é:

```text
https://your-public-host.example.com/mcp
```

## Configuração YAML

Um YAML config pode guardar defaults de runtime não secretos:

```yaml
host: 127.0.0.1
port: 8765
mode: mcp
workspace_root: /srv/local-shell-mcp/workspace
auth_mode: oauth
public_base_url: https://your-public-host.example.com
```

Execute:

```bash
local-shell-mcp --config /path/to/config.yaml
```

Environment variables com prefixo `LOCAL_SHELL_MCP_` sobrescrevem valores YAML.

## Responsabilidade pelo host toolchain

O binary empacota a aplicação Python, não todas as ferramentas de desenvolvimento. Ferramentas MCP chamam programas disponíveis no host.

Instale o que suas tarefas exigem:

| Capability | Host packages to consider |
|---|---|
| Search and shell ergonomics | `ripgrep`, `tree`, `jq`, `curl`, `wget`; releases Linux já incluem static tmux helper |
| Git workflows | `git`, `gh`, OpenSSH client, credential helpers |
| Python projects | Python, pip, venv, project-specific compilers and headers |
| Node projects | Node.js, npm, pnpm, yarn |
| Rust/Go/Java/C++ | Cargo/rustc, Go, JDK, Maven/Gradle, compilers, CMake, Ninja |
| Browser automation | Playwright browser binaries and OS dependencies |
| Document conversion | LibreOffice, Pandoc, Poppler utilities |

Se não quiser manter esse host toolchain, use Docker Compose.

## Serviço de longa duração

Para um deployment público persistente, execute o binary sob o process supervisor do sistema operacional. Mantenha estas práticas:

- Use uma conta OS dedicada e de poucos privilégios.
- Use um workspace directory dedicado.
- Guarde valores sensíveis fora de arquivos world-readable.
- Reinicie automaticamente em caso de falha.
- Verifique `/healthz` após cada reinício.
- Mantenha logs para troubleshooting.

## Atualizações

1. Baixe o novo release archive para sua plataforma.
2. Verifique checksums se desejar.
3. Substitua o executable.
4. Reinicie o process manager.
5. Verifique `/healthz`.
6. Peça ao client para executar `environment_get` antes de continuar.

## Notas de segurança

O binary executa com os privilégios do usuário do sistema operacional. Em deployments públicos, use um usuário dedicado de poucos privilégios, um workspace dedicado e, quando possível, uma fronteira VM/container.

Não defina `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER=true` para um binary executado diretamente no seu host pessoal. Essa configuração é destinada a containers ou VMs descartáveis.
