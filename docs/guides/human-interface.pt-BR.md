<!-- i18n-source-sha256: 8c683835be3adb3bf08d9d69b1731f61a39753bf255170fc663cf9456a0df54f -->
# Interface humana

`local-shell-mcp` oferece duas interfaces humanas compatíveis sobre a mesma API de serviço, workspace, registro de terminais persistentes, registro de workers remotos e log de auditoria MCP:

- **Web UI** é um painel nativo do navegador otimizado para inspeção operacional rápida.
- **OpenTUI** é o aplicativo completo orientado a terminal e continua disponível tanto no navegador quanto como comando nativo de terminal.

Nenhum modo cria um control plane separado. Trocar de interface não altera máquinas conectadas, Sessions, jobs, permissões ou dados de auditoria.

## Iniciar o serviço

Inicie `local-shell-mcp` normalmente:

```bash
local-shell-mcp --mode mcp
```

## Live Workspace do ChatGPT

Quando o ChatGPT pode renderizar MCP Apps, `workspace_open` abre uma view colaborativa flutuante para a Session lógica atualmente anexada. A Session é dona do estado durável da tarefa; o Live Workspace apenas apresenta atividade ao vivo e controles humanos. Assim, reconectar o app ou trocar o transporte ChatGPT/MCP não reinicia a Session.

Um handoff típico é:

```text
session_manage(action="start", objective=...)
        -> session_id
... tool work + session_manage(action="report", ...) ...
new agent run
session_manage(action="resume", session_id=..., takeover=true)
        -> inherited progress, Plan, and recent activity
workspace_open()
        -> reconnectable view of that Session
```

`takeover=true` substitui um agent run antigo ainda ativo. Qualquer chamada de ferramenta posterior do run substituído é rejeitada até que esse agente faça resume explícito da Session novamente. Sessions não se vinculam a machine ou working directory; parâmetros normais das ferramentas continuam escolhendo targets local/remoto e paths.

Um Plan opcional de `plan_manage` habilita Goal mode para a Session. Se o Plan estiver active e não houver atividade do agente por 15 minutos, um Live Workspace anexado pode pedir ao ChatGPT para continuar. A continuação primeiro faz resume do mesmo `session_id` e é limitada a 10 tentativas, aceitas ou rejeitadas. Plans blocked, completed ou cancelled não são continuados automaticamente; um Plan active com todos os steps completed/skipped continua elegível para uma continuação de limpeza para que o agente retomado faça finish do Plan. Controles humanos pause/resume/cancel atualizam o Plan pertencente à Session, não estado efêmero do Live Workspace.

## Interface do navegador

Abra:

```text
http://127.0.0.1:8765/ui
```

Para uma implantação pública, use o origin HTTPS configurado:

```text
https://your-public-host.example.com/ui
```

A interface do navegador usa o mesmo servidor OAuth e os mesmos scopes que o MCP. O shell da página e os recursos estáticos são públicos para que a tela de login possa carregar, enquanto `/api/ui/*` e o WebSocket de terminal do OpenTUI permanecem protegidos. Tokens de acesso ficam apenas no session storage do navegador.

### Escolher uma interface

A tela OAuth oferece duas entradas:

- **Open Web UI** autoriza e abre o painel nativo.
- **Continue to OpenTUI** autoriza e abre a interface de terminal, preservando o comportamento anterior do navegador.

Após a autorização, o seletor na barra lateral alterna entre Web UI e OpenTUI sem novo login. A página nativa atual é lembrada ao mudar temporariamente para OpenTUI.

As rotas podem ser adicionadas aos favoritos:

```text
/ui/#/overview
/ui/#/machines
/ui/#/workloads
/ui/#/activity
/ui/#/console
```

`#/web` e `#/dashboard` são aliases de Overview. `#/tui` e `#/opentui` são aliases de Console.

## Web UI nativa

A Web UI nativa consulta a API de interface humana existente a cada cinco segundos e renderiza controles nativos do navegador em vez de células de terminal. Nenhum PTY é iniciado até OpenTUI ser selecionado.

### Overview

Overview mostra primeiro as informações operacionais de maior prioridade:

- Saúde do controller e versão atual do LSM.
- Contagem de máquinas online e offline.
- Tracked jobs ativos e sessões persistentes de terminal.
- CPU, memória, disco do workspace, load, throughput de rede e uptime.
- Alertas gerados pelo estado de workers, limites de recursos, jobs com falha e chamadas MCP com falha.
- Atividade MCP recente originada pelo modelo.

### Machines

Machines lista o controller local e os workers remotos conectados com status, plataforma, versão, diretório de trabalho, capacidades e informações de last-seen.

### Workloads

Workloads combina tracked jobs ativos e sessões shell persistentes independentes. A Web UI é somente leitura para esses registros; use OpenTUI para gerenciamento interativo de sessões.

### Activity

Activity combina alertas atuais e atividade recente de auditoria MCP. Comandos digitados por humanos e operações de arquivos permanecem fora do log de auditoria MCP.

## OpenTUI no navegador

Selecionar **OpenTUI** inicia sob demanda o mesmo aplicativo OpenTUI usado pelo launcher de terminal nativo. O console do navegador mantém:

- Transporte PTY binário autenticado via WebSocket.
- Redimensionamento automático do terminal e backoff de reconexão.
- Interação por mouse com controles OpenTUI.
- Modo tela cheia e atalhos de teclado seguros para o navegador.
- Teclas de atalho móveis e controle explícito do teclado virtual.
- Suporte a SIXEL e inline image por xterm.js.

O navegador não cria um PTY OpenTUI enquanto o usuário permanecer no modo Web UI nativo.

## OpenTUI nativo

Executáveis release independentes incorporam o runtime OpenTUI da plataforma. Mantenha apenas o executável principal, inicie o serviço e execute:

```bash
local-shell-mcp tui
```

O TUI nativo não pede login ao operador humano. O launcher fornece de forma transparente uma credencial local gerada à API loopback. Essa credencial é armazenada no state directory configurado com permissões somente do proprietário; um proxy reverso conectado via loopback não recebe esse bypass.

Um checkout do código-fonte também pode executar o TUI depois de instalar as dependências Bun:

```bash
cd ui
bun install --frozen-lockfile
bun run build
cd ..
local-shell-mcp tui
```

Use `--api-base` somente quando o serviço local usar uma porta diferente da padrão:

```bash
local-shell-mcp tui --api-base http://127.0.0.1:9876/api/ui
```

## Telas do OpenTUI

### Dashboard

Dashboard é a visão operacional do OpenTUI. Terminais largos mostram regiões separadas para node, workload, alert, activity, informações do sistema e tendências; terminais menores recolhem tudo em resumos compactos sem rolagem horizontal.

### Files

Files é um gerenciador de arquivos nativo do LSM com três painéis para máquinas locais e remotas. Ele oferece criar, editar, renomear, copiar, mover, colar, excluir, alternar arquivos ocultos, atualizar, pré-visualizar texto, pré-visualizar binários e miniaturas de imagens limitadas.

### Terminals

Terminals gerencia sessões shell persistentes em máquinas locais e remotas. Suporta entrada de comandos completos, entrada interativa raw, troca de sessão, criação e encerramento de sessões, saída recente e um painel de auditoria MCP recolhível.

### Audit

Audit lê o log de auditoria JSONL limitado e oferece filtros node, operation, event, session, search, time-range e sort, além de inspeção detalhada dos registros.

### Remotes

Remotes mostra workers remotos online e offline, capacidades, diretórios de trabalho e metadados do sistema. Pode criar um join invite de uso único, renomear um node ou revogar sua identidade persistente.

## Navegação do OpenTUI

A barra superior de categorias e as ações contextuais do rodapé podem ser clicadas com o mouse em terminais nativos e no console do navegador.

| Teclas | Ação |
|---|---|
| `Alt+1` … `Alt+5` | Abre Dashboard, Files, Terminals, Remotes ou Audit. |
| `F2` … `F6` | Atalhos alternativos de categoria. |
| `F1` | Abrir o guia de teclado. |
| `F9` | Atualizar a lista de máquinas. |
| `Alt+Q` | Sair do processo OpenTUI nativo sem invocar um atalho Ctrl reservado pelo navegador. |

Terminals usa `Alt+N` para nova sessão, `Alt+W` para encerrar a sessão selecionada, `Alt+A` para alternar o painel de auditoria, `Alt+R` para atualizar e `Alt+Left/Right` para trocar de sessão. O console do navegador intercepta essas combinações antes da navegação ou menus do navegador.

## Configuração

| Chave YAML | Variável de ambiente | Padrão | Finalidade |
|---|---|---|---|
| `ui_enabled` | `LOCAL_SHELL_MCP_UI_ENABLED` | `true` | Montar ou desativar as interfaces humanas. |
| `ui_path` | `LOCAL_SHELL_MCP_UI_PATH` | `/ui` | Caminho de montagem da interface do navegador no serviço MCP. |
| `ui_tui_command` | `LOCAL_SHELL_MCP_UI_TUI_COMMAND` | auto | Substituir a resolução do executável OpenTUI nativo. |
| `ui_wallpaper` | `LOCAL_SHELL_MCP_UI_WALLPAPER` | `bing` | Configuração de papel de parede mantida para implantações do console OpenTUI no navegador. |
| `ui_terminal_idle_timeout_s` | `LOCAL_SHELL_MCP_UI_TERMINAL_IDLE_TIMEOUT_S` | `3600` | Fechar um PTY OpenTUI inativo do navegador após estes segundos; `0` desativa o timeout. |
| `ui_terminal_max_sessions` | `LOCAL_SHELL_MCP_UI_TERMINAL_MAX_SESSIONS` | `8` | Máximo de sessões PTY OpenTUI simultâneas no navegador. |

## Notas de empacotamento

- Imagens Docker incluem os recursos da Web UI e o runtime OpenTUI nativo.
- Executáveis independentes incorporam os recursos da Web UI e um runtime OpenTUI de plataforma compactado.
- Wheels Python incluem os recursos do navegador; OpenTUI nativo exige um executável release ou checkout do código-fonte com dependências Bun instaladas.
- As duas interfaces são servidas pelo mesmo processo e porta do MCP; nenhum serviço web adicional é necessário.
