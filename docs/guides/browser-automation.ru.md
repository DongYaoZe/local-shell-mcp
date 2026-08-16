<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Автоматизация браузера

Браузерные инструменты используют Playwright для исследования страниц, сбора доказательств и выполнения воспроизводимых браузерных сценариев. Публичный tool surface намеренно невелик.

## Инструменты

| Tool | Назначение |
|---|---|
| `browser_session` | Запускать, перечислять, закрывать и очищать постоянные браузерные сессии; при необходимости повторно использовать profile или storage state. |
| `browser_snapshot` | Читать ограниченный текст страницы, page/network errors и интерактивные элементы с короткими refs вроде `e1`; при необходимости делать screenshot. |
| `browser_act` | Выполнять структурированные navigation, click, fill, select, key, wait и многостраничные действия по snapshot refs или CSS selectors. |
| `browser_run_script` | Запускать полный Python Playwright script, когда набора высокоуровневых действий недостаточно. |

Все браузерные инструменты принимают необязательный `machine`. Зависимости браузера должны быть заранее установлены на выбранном controller или worker; установка выполняется обычными shell-командами, например `python -m playwright install chromium`.

## Типичные сценарии

Для интерактивной работы вызовите `browser_session(action="start", url=...)`, затем `browser_snapshot`. Snapshot возвращает короткие ссылки вроде `e1` и `e2`; передавайте их напрямую в `browser_act`, например `{"action": "click", "target": "e1"}` или `{"action": "fill", "target": "e2", "value": "..."}`. После navigation снимайте новый snapshot, поскольку element refs относятся к состоянию страницы и не являются постоянными selectors.

Для обычной проверки и screenshots предпочитайте `browser_session` вместе с `browser_snapshot`; snapshot может вернуть ограниченный видимый текст и сохранить screenshot. Используйте `browser_run_script` для JavaScript evaluation, нестандартной capture/PDF logic или взаимодействий, не представленных в `browser_act`.

Ограничивайте scripts, задавайте явные timeout, сохраняйте artifacts в workspace и не вводите credentials, если среда не выделена специально для этой задачи.
