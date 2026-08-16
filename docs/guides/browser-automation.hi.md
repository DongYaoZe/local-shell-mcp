<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Browser automation

Browser tools Playwright का उपयोग pages inspect करने, evidence capture करने और reproducible browser workflows चलाने के लिए करते हैं। Public tool surface जानबूझकर छोटा रखा गया है।

## Tools

| Tool | उद्देश्य |
|---|---|
| `browser_session` | Persistent browser sessions शुरू, list, close या clean up करना; वैकल्पिक रूप से profile या storage state reuse करना। |
| `browser_snapshot` | Bounded page text, page/network errors और `e1` जैसे short refs वाले interactive elements पढ़ना; वैकल्पिक screenshot लेना। |
| `browser_act` | Snapshot refs या CSS selectors का उपयोग करके structured navigation, click, fill, select, key, wait और multi-page actions चलाना। |
| `browser_run_script` | जब high-level action set पर्याप्त न हो तब पूरा Python Playwright script चलाना। |

सभी browser tools वैकल्पिक `machine` स्वीकार करते हैं। Browser dependencies चुने गए controller या worker पर पहले से installed होनी चाहिए; installation सामान्य shell commands जैसे `python -m playwright install chromium` से की जाती है।

## सामान्य flows

Interactive work के लिए `browser_session(action="start", url=...)` call करें, फिर `browser_snapshot`। Snapshot `e1` और `e2` जैसे short references देता है; इन्हें सीधे `browser_act` को दें, जैसे `{"action": "click", "target": "e1"}` या `{"action": "fill", "target": "e2", "value": "..."}`। Navigation के बाद फिर snapshot लें, क्योंकि element refs page-state references हैं, permanent selectors नहीं।

सामान्य inspection और screenshots के लिए `browser_session` + `browser_snapshot` को प्राथमिकता दें; snapshot bounded visible text लौटा सकता है और screenshot सहेज सकता है। JavaScript evaluation, custom capture/PDF logic या `browser_act` में उपलब्ध न होने वाले interactions के लिए `browser_run_script` उपयोग करें।

Scripts को bounded रखें, explicit timeouts सेट करें, artifacts workspace के भीतर सहेजें और credentials दर्ज करने से बचें जब तक environment task के लिए dedicated न हो।
