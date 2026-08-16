<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Automazione del browser

Gli strumenti browser usano Playwright per ispezionare pagine, acquisire prove ed eseguire workflow del browser riproducibili. La tool surface pubblica è volutamente ridotta.

## Strumenti

| Tool | Scopo |
|---|---|
| `browser_session` | Avviare, elencare, chiudere o pulire sessioni browser persistenti; facoltativamente riutilizzare un profile o storage state. |
| `browser_snapshot` | Leggere testo limitato della pagina, errori page/network ed elementi interattivi con refs brevi come `e1`; facoltativamente acquisire una screenshot. |
| `browser_act` | Eseguire navigation, click, fill, select, key, wait e azioni multipagina strutturate usando snapshot refs o CSS selectors. |
| `browser_run_script` | Eseguire uno script Python Playwright completo quando il set di azioni di alto livello non basta. |

Tutti gli strumenti browser accettano un `machine` opzionale. Le dipendenze del browser devono essere già installate sul controller o worker selezionato; l’installazione avviene con normali comandi shell come `python -m playwright install chromium`.

## Flussi comuni

Per il lavoro interattivo, chiama `browser_session(action="start", url=...)`, quindi `browser_snapshot`. Lo snapshot restituisce riferimenti brevi come `e1` e `e2`; passali direttamente a `browser_act`, ad esempio `{"action": "click", "target": "e1"}` o `{"action": "fill", "target": "e2", "value": "..."}`. Crea un nuovo snapshot dopo la navigation perché le refs degli elementi rappresentano lo stato della pagina e non sono selectors permanenti.

Per ispezioni ordinarie e screenshots, preferisci `browser_session` più `browser_snapshot`; lo snapshot può restituire testo visibile limitato e salvare una screenshot. Usa `browser_run_script` per JavaScript evaluation, logica personalizzata di capture/PDF o interazioni non rappresentate da `browser_act`.

Mantieni gli script limitati, imposta timeouts espliciti, salva gli artifacts nel workspace ed evita di inserire credentials salvo che l’ambiente sia dedicato all’attività.
