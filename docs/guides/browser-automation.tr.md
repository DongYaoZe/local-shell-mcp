<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Tarayıcı otomasyonu

Tarayıcı araçları sayfaları incelemek, kanıt toplamak ve tekrarlanabilir tarayıcı iş akışları yürütmek için Playwright kullanır. Genel tool surface kasıtlı olarak küçüktür.

## Araçlar

| Tool | Amaç |
|---|---|
| `browser_session` | Kalıcı tarayıcı oturumlarını başlatmak, listelemek, kapatmak veya temizlemek; isteğe bağlı olarak profile ya da storage state’i yeniden kullanmak. |
| `browser_snapshot` | Sınırlı sayfa metnini, page/network hatalarını ve `e1` gibi kısa ref’lere sahip etkileşimli öğeleri okumak; isteğe bağlı screenshot almak. |
| `browser_act` | Snapshot ref veya CSS selector kullanarak yapılandırılmış navigation, click, fill, select, key, wait ve çok sayfalı işlemler yürütmek. |
| `browser_run_script` | Üst düzey action set yeterli olmadığında tam bir Python Playwright script çalıştırmak. |

Tüm tarayıcı araçları isteğe bağlı `machine` kabul eder. Tarayıcı bağımlılıkları seçilen controller veya worker üzerinde önceden kurulu olmalıdır; kurulum `python -m playwright install chromium` gibi normal shell komutlarıyla yapılır.

## Yaygın akışlar

Etkileşimli çalışma için `browser_session(action="start", url=...)` çağırın, ardından `browser_snapshot` kullanın. Snapshot `e1` ve `e2` gibi kısa referanslar döndürür; bunları doğrudan `browser_act` içine verin, örneğin `{"action": "click", "target": "e1"}` veya `{"action": "fill", "target": "e2", "value": "..."}`. Element ref’leri kalıcı selector değil sayfa durumu referansları olduğundan navigation sonrasında yeniden snapshot alın.

Normal inceleme ve screenshots için `browser_session` + `browser_snapshot` tercih edin; snapshot sınırlı visible text döndürebilir ve screenshot kaydedebilir. JavaScript evaluation, özel capture/PDF logic veya `browser_act` ile ifade edilmeyen etkileşimler için `browser_run_script` kullanın.

Script’leri sınırlı tutun, açık timeout’lar belirleyin, artifacts’ı workspace altında saklayın ve ortam göreve ayrılmadıkça credential girmekten kaçının.
