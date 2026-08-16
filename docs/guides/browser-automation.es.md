<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Automatización del navegador

Las herramientas de navegador usan Playwright para inspeccionar páginas, capturar evidencias y ejecutar flujos de navegador reproducibles. La tool surface pública se mantiene deliberadamente pequeña.

## Herramientas

| Tool | Propósito |
|---|---|
| `browser_session` | Iniciar, listar, cerrar o limpiar sesiones persistentes de navegador; opcionalmente reutilizar un profile o storage state. |
| `browser_snapshot` | Leer texto acotado de la página, errores de page/network y elementos interactivos con refs cortas como `e1`; opcionalmente capturar una screenshot. |
| `browser_act` | Ejecutar navigation, click, fill, select, key, wait y acciones multipágina estructuradas mediante refs de snapshot o CSS selectors. |
| `browser_run_script` | Ejecutar un script Python Playwright completo cuando el conjunto de acciones de alto nivel no sea suficiente. |

Todas las herramientas de navegador aceptan `machine` opcional. Las dependencias del navegador deben estar instaladas previamente en el controller o worker seleccionado; se instalan mediante comandos shell normales como `python -m playwright install chromium`.

## Flujos habituales

Para trabajo interactivo, llame a `browser_session(action="start", url=...)` y después a `browser_snapshot`. El snapshot devuelve referencias cortas como `e1` y `e2`; páselas directamente a `browser_act`, por ejemplo `{"action": "click", "target": "e1"}` o `{"action": "fill", "target": "e2", "value": "..."}`. Vuelva a tomar un snapshot tras navegar, porque las refs de elementos son referencias al estado de la página, no selectores permanentes.

Para inspección normal y screenshots, prefiera `browser_session` más `browser_snapshot`; el snapshot puede devolver texto visible acotado y guardar una screenshot. Use `browser_run_script` para evaluación JavaScript, lógica personalizada de captura/PDF o interacciones que `browser_act` no represente.

Mantenga los scripts acotados, establezca timeouts explícitos, guarde los artifacts dentro del workspace y evite introducir credentials salvo que el entorno esté dedicado a la tarea.
