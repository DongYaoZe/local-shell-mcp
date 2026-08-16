<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Automação do navegador

As ferramentas de navegador usam Playwright para inspecionar páginas, capturar evidências e executar fluxos de navegador reproduzíveis. A tool surface pública é deliberadamente pequena.

## Ferramentas

| Tool | Finalidade |
|---|---|
| `browser_session` | Iniciar, listar, fechar ou limpar sessões persistentes do navegador; opcionalmente reutilizar um profile ou storage state. |
| `browser_snapshot` | Ler texto limitado da página, erros de page/network e elementos interativos com refs curtas como `e1`; opcionalmente capturar uma screenshot. |
| `browser_act` | Executar navigation, click, fill, select, key, wait e ações multipágina estruturadas usando refs de snapshot ou CSS selectors. |
| `browser_run_script` | Executar um script Python Playwright completo quando o conjunto de ações de alto nível não for suficiente. |

Todas as ferramentas de navegador aceitam `machine` opcional. As dependências de navegador devem estar instaladas no controller ou worker selecionado; a instalação é feita com comandos shell comuns, como `python -m playwright install chromium`.

## Fluxos comuns

Para trabalho interativo, chame `browser_session(action="start", url=...)` e depois `browser_snapshot`. O snapshot retorna referências curtas como `e1` e `e2`; passe-as diretamente para `browser_act`, por exemplo `{"action": "click", "target": "e1"}` ou `{"action": "fill", "target": "e2", "value": "..."}`. Faça um novo snapshot após navigation porque as refs dos elementos são referências ao estado da página, não selectors permanentes.

Para inspeção comum e screenshots, prefira `browser_session` mais `browser_snapshot`; o snapshot pode retornar texto visível limitado e salvar uma screenshot. Use `browser_run_script` para JavaScript evaluation, lógica personalizada de captura/PDF ou interações não representadas por `browser_act`.

Mantenha os scripts limitados, defina timeouts explícitos, salve artifacts no workspace e evite inserir credentials, a menos que o ambiente seja dedicado à tarefa.
