# Browser automation

Browser tools use Playwright to inspect pages, capture evidence, and run reproducible browser workflows. The public surface is deliberately small.

## Tools

| Tool | Purpose |
|---|---|
| `browser_session` | Start, list, close, or clean up persistent browser sessions; optionally reuse a profile or storage state. |
| `browser_snapshot` | Read bounded page text, page/network errors, and interactive elements with short refs such as `e1`; optionally capture a screenshot. |
| `browser_act` | Run structured navigation, click, fill, select, key, wait, and multi-page actions using snapshot refs or CSS selectors. |
| `browser_get_text_tool` | Extract visible text from a selector. |
| `browser_capture_tool` | Save either a PNG screenshot or Chromium PDF. |
| `playwright_run_script_tool` | Run a complete Python Playwright script when the high-level action set is insufficient. |

All browser tools accept optional `machine`. Browser dependencies must already be installed on the selected controller or worker; installation is performed with ordinary shell commands such as `python -m playwright install chromium`.

## Common flows

For interactive work, call `browser_session(action="start", url=...)`, then `browser_snapshot`. The snapshot returns short references such as `e1` and `e2`; pass those refs directly to `browser_act`, for example `{"action": "click", "target": "e1"}` or `{"action": "fill", "target": "e2", "value": "..."}`. Re-snapshot after navigation because element refs are page-state references, not permanent selectors.

For one-shot visual verification, start the site with `shell_start` or `job_start`, wait for readiness, call `browser_capture_tool(capture_format="png")`, then stop the process. Use `capture_format="pdf"` with Chromium for printable output. Use `browser_get_text_tool` when only rendered content matters, and keep `playwright_run_script_tool` for JavaScript evaluation or interactions not represented by `browser_act`.

Keep scripts bounded, set explicit timeouts, save artifacts under the workspace, and avoid entering credentials unless the environment is dedicated to the task.
