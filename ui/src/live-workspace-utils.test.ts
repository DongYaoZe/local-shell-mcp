import { describe, expect, test } from "bun:test"
import {
  activityDestination,
  activityIntent,
  eventDetail,
  eventTitle,
  formatBytes,
  isOperationalActivityEvent,
  joinPath,
  parentPath,
  renderDiffHtml,
  toggleWorkspaceDisplayMode,
  reconnectDelayMs,
  toolResultFromOpenAiGlobals,
  truncateContext,
  type LiveEvent,
} from "./live-workspace-utils"

describe("live workspace utilities", () => {
  test("display mode toggles only between floating and fullscreen", () => {
    expect(toggleWorkspaceDisplayMode("pip")).toBe("fullscreen")
    expect(toggleWorkspaceDisplayMode("fullscreen")).toBe("pip")
  })

  test("reconnect backoff grows but remains bounded", () => {
    expect(reconnectDelayMs(0)).toBe(500)
    expect(reconnectDelayMs(1)).toBe(1000)
    expect(reconnectDelayMs(4)).toBe(8000)
    expect(reconnectDelayMs(5)).toBe(15000)
    expect(reconnectDelayMs(50)).toBe(15000)
  })

  test("paths work for POSIX and Windows", () => {
    expect(parentPath("/workspace/src/file.py")).toBe("/workspace/src")
    expect(parentPath("file.py")).toBe(".")
    expect(parentPath("C:\\work\\src\\file.py")).toBe("C:\\work\\src")
    expect(parentPath("C:\\work")).toBe("C:\\")
    expect(parentPath("C:\\")).toBe("C:\\")
    expect(parentPath("C:/work")).toBe("C:/")
    expect(parentPath("C:/")).toBe("C:/")
    expect(parentPath("\\\\server\\share\\")).toBe("\\\\server\\share\\")
    expect(parentPath("\\\\server\\share")).toBe("\\\\server\\share")
    expect(parentPath("//server/share/")).toBe("//server/share/")
    expect(parentPath("//server/share")).toBe("//server/share")
    expect(joinPath("/workspace", "src")).toBe("/workspace/src")
    expect(joinPath("C:\\work", "src")).toBe("C:\\work\\src")
  })

  test("activity summaries stay operational", () => {
    const event: LiveEvent = {
      seq: 4,
      ts: 1,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell_tool", cwd: "/workspace", duration_ms: 1420 },
    }
    expect(eventTitle(event)).toBe("run_shell_tool completed")
    expect(activityIntent(event)).toBe("Running command")
    expect(activityDestination(event)).toBe("detail")
    expect(eventDetail(event)).toContain("/workspace")
    expect(eventDetail(event)).toContain("1.4 s")
  })

  test("activity hides workspace bootstrap noise and routes useful operations", () => {
    const opened: LiveEvent = { seq: 1, ts: 1, type: "channel.opened", actor: "system", data: {} }
    const bootstrap: LiveEvent = { seq: 2, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "open_live_workspace" } }
    const terminalInput: LiveEvent = { seq: 3, ts: 1, type: "human.action", actor: "human", data: { action: "terminal.input", bytes: 1 } }
    const edit: LiveEvent = { seq: 4, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "edit_file", path: "/workspace/src/app.ts" } }
    const job: LiveEvent = { seq: 5, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "job_start", name: "tests" } }

    expect(isOperationalActivityEvent(opened)).toBeFalse()
    expect(isOperationalActivityEvent(bootstrap)).toBeFalse()
    expect(isOperationalActivityEvent(terminalInput)).toBeFalse()
    expect(isOperationalActivityEvent(edit)).toBeTrue()
    expect(activityIntent(edit)).toBe("Editing app.ts")
    expect(activityDestination(edit)).toBe("files")
    expect(activityIntent(job)).toBe("Starting tests")
    expect(activityDestination(job)).toBe("jobs")
  })

  test("diff renderer escapes content and classifies lines", () => {
    const html = renderDiffHtml("@@ -1 +1 @@\n-old <tag>\n+new & value")
    expect(html).toContain("diff-line hunk")
    expect(html).toContain("diff-line removed")
    expect(html).toContain("diff-line added")
    expect(html).toContain("&lt;tag&gt;")
    expect(html).toContain("&amp; value")
  })

  test("large model context is bounded", () => {
    const value = truncateContext("x".repeat(100), 20)
    expect(value.startsWith("x".repeat(20))).toBeTrue()
    expect(value).toContain("truncated")
    expect(formatBytes(1024)).toBe("1.0 KiB")
  })

  test("ChatGPT compatibility globals preserve hidden live credentials", () => {
    const result = toolResultFromOpenAiGlobals({
      toolOutput: { live_id: "live-1", machine: "local", cwd: "." },
      toolResponseMetadata: {
        status: "finished",
        mcp_tool_result: {
          _meta: {
            "local-shell-mcp/live": {
              token: "secret-live-token",
              apiBase: "https://lsm.example.test",
            },
          },
        },
      },
    })

    expect(result?._meta).toEqual({
      "local-shell-mcp/live": {
        token: "secret-live-token",
        apiBase: "https://lsm.example.test",
      },
    })
    expect(result?.structuredContent).toEqual({ live_id: "live-1", machine: "local", cwd: "." })
  })

  test("ChatGPT compatibility globals accept call_tool_result fallback", () => {
    const result = toolResultFromOpenAiGlobals({
      toolResponseMetadata: {
        call_tool_result: {
          _meta: { "local-shell-mcp/live": { token: "token", apiBase: "https://lsm.example.test" } },
          structuredContent: { live_id: "live-2" },
        },
      },
    })

    expect(result?.structuredContent).toEqual({ live_id: "live-2" })
  })
})
