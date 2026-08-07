# 瀏覽器自動化

瀏覽器工具基於 Playwright，用於檢查頁面、保存證據和執行可重現的互動流程。公開工具面刻意保持精簡。

## 工具

| 工具 | 用途 |
|---|---|
| `browser_session` | 啟動、列出、關閉或清理持久瀏覽器會話；可重用 profile 或 storage state。 |
| `browser_snapshot` | 讀取有界頁面文字、頁面/網路錯誤，以及帶 `e1` 等短引用的可互動元素；可選截圖。 |
| `browser_act` | 使用 snapshot 引用或 CSS selector 執行導覽、點擊、填寫、選擇、按鍵、等待和多頁面操作。 |
| `browser_run_script` | 當高層 action 集合不足時，執行完整 Python Playwright 腳本。 |

所有瀏覽器工具都接受可選的 `machine` 參數。控制端或目標 worker 必須已經安裝瀏覽器相依套件；安裝工作透過一般 shell 命令完成，例如 `python -m playwright install chromium`。

## 常見流程

需要互動時，先呼叫 `browser_session(action="start", url=...)`，再呼叫 `browser_snapshot`。snapshot 會回傳 `e1`、`e2` 這類短引用，可直接作為 `browser_act` 的 `target`，例如 `{"action": "click", "target": "e1"}` 或 `{"action": "fill", "target": "e2", "value": "..."}`。頁面導覽後應重新 snapshot，因為這些引用表示目前頁面狀態，並不是永久 selector。

一般頁面檢查和截圖優先使用 `browser_session` 搭配 `browser_snapshot`；snapshot 可以回傳有界可見文字並保存截圖。需要 JavaScript 求值、自訂截圖/PDF 邏輯或 `browser_act` 尚未涵蓋的互動時使用 `browser_run_script`。

腳本應設定明確逾時，把產物保存到工作區，並避免在非專用環境中輸入憑據。
