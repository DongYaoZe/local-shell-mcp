# 浏览器自动化

浏览器工具基于 Playwright，用于检查页面、保存证据和执行可复现的交互流程。公开工具面刻意保持精简。

## 工具

| 工具 | 用途 |
|---|---|
| `browser_session` | 启动、列出、关闭或清理持久浏览器会话；可复用 profile 或 storage state。 |
| `browser_snapshot` | 读取有界页面文本、页面/网络错误，以及带 `e1` 等短引用的可交互元素；可选截图。 |
| `browser_act` | 使用 snapshot 引用或 CSS selector 执行导航、点击、填写、选择、按键、等待和多页面操作。 |
| `browser_run_script` | 当高层 action 集合不足时，运行完整 Python Playwright 脚本。 |

所有浏览器工具都接受可选的 `machine` 参数。控制端或目标 worker 必须已经安装浏览器依赖；安装工作通过普通 shell 命令完成，例如 `python -m playwright install chromium`。

## 常见流程

需要交互时，先调用 `browser_session(action="start", url=...)`，再调用 `browser_snapshot`。snapshot 会返回 `e1`、`e2` 这样的短引用，可直接作为 `browser_act` 的 `target`，例如 `{"action": "click", "target": "e1"}` 或 `{"action": "fill", "target": "e2", "value": "..."}`。页面导航后应重新 snapshot，因为这些引用表示当前页面状态，并不是永久 selector。

常规页面检查和截图优先使用 `browser_session` 配合 `browser_snapshot`；snapshot 可以返回有界可见文本并保存截图。需要 JavaScript 求值、自定义截图/PDF 逻辑或 `browser_act` 尚未覆盖的交互时使用 `browser_run_script`。

脚本应设置明确超时，把产物保存到工作区，并避免在非专用环境中输入凭据。
