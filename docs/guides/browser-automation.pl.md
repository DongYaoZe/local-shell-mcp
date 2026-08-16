<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Automatyzacja przeglądarki

Narzędzia przeglądarki używają Playwright do inspekcji stron, zbierania dowodów i wykonywania powtarzalnych workflow przeglądarki. Publiczny tool surface jest celowo niewielki.

## Narzędzia

| Tool | Zastosowanie |
|---|---|
| `browser_session` | Uruchamiać, listować, zamykać lub czyścić trwałe sesje przeglądarki; opcjonalnie ponownie używać profile lub storage state. |
| `browser_snapshot` | Czytać ograniczony tekst strony, błędy page/network i elementy interaktywne z krótkimi refs, np. `e1`; opcjonalnie wykonywać screenshot. |
| `browser_act` | Wykonywać ustrukturyzowane navigation, click, fill, select, key, wait i akcje wielostronicowe przy użyciu snapshot refs lub CSS selectors. |
| `browser_run_script` | Uruchamiać pełny Python Playwright script, gdy zestaw działań wysokiego poziomu jest niewystarczający. |

Wszystkie narzędzia przeglądarki przyjmują opcjonalne `machine`. Zależności przeglądarki muszą być wcześniej zainstalowane na wybranym controller lub worker; instalację wykonuje się zwykłymi poleceniami shell, np. `python -m playwright install chromium`.

## Typowe przepływy

Do pracy interaktywnej wywołaj `browser_session(action="start", url=...)`, a następnie `browser_snapshot`. Snapshot zwraca krótkie referencje, takie jak `e1` i `e2`; przekazuj je bezpośrednio do `browser_act`, np. `{"action": "click", "target": "e1"}` lub `{"action": "fill", "target": "e2", "value": "..."}`. Po navigation wykonaj nowy snapshot, ponieważ element refs są referencjami stanu strony, a nie trwałymi selectorami.

Do zwykłej inspekcji i screenshots preferuj `browser_session` wraz z `browser_snapshot`; snapshot może zwrócić ograniczony visible text i zapisać screenshot. Używaj `browser_run_script` do JavaScript evaluation, niestandardowej logiki capture/PDF lub interakcji, których nie reprezentuje `browser_act`.

Ograniczaj scripts, ustawiaj jawne timeouty, zapisuj artifacts w workspace i unikaj wprowadzania credentials, chyba że środowisko jest przeznaczone wyłącznie do danego zadania.
