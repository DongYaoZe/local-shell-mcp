import { describe, expect, test } from "bun:test"
import {
  activityDestination,
  activityEventKey,
  activityIntent,
  continuationCountdownState,
  eventDetail,
  eventTitle,
  formatBytes,
  formatCountdown,
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
  test("Live Workspace teardown does not recursively call its rendering tool", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain("app.onteardown = async")
    expect(source).toContain('name: "live_workspace_reconnect"')
    expect(source).not.toContain('name: "open_live_workspace"')
  })

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

  test("auto continuation countdown appears only after five idle minutes", () => {
    const plan = {
      status: "active",
      continuation_pending: false,
      auto_continue_exhausted: false,
      in_flight_calls: 0,
      last_agent_activity: 1_000,
      execution_lease_s: 900,
      continuation_due_at: 1_900,
    }
    expect(continuationCountdownState(plan, 1_299).visible).toBeFalse()
    const visible = continuationCountdownState(plan, 1_300)
    expect(visible.visible).toBeTrue()
    expect(visible.remainingSeconds).toBe(600)
    expect(formatCountdown(600)).toBe("10:00")
    expect(continuationCountdownState({ ...plan, continuation_retry_after: 2_000 }, 1_300).remainingSeconds).toBe(700)
    expect(continuationCountdownState({ ...plan, in_flight_calls: 1 }, 1_500).visible).toBeFalse()
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

  test("activity row identity stays unique across events from one tool call", () => {
    const started: LiveEvent = {
      seq: 40,
      ts: 1,
      type: "tool.started",
      actor: "agent",
      data: { tool: "run_shell_tool", call_id: "call-1" },
    }
    const completed: LiveEvent = {
      seq: 41,
      ts: 2,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell_tool", call_id: "call-1" },
    }

    expect(activityEventKey(started)).not.toBe(activityEventKey(completed))
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
    const reconnect: LiveEvent = { seq: 3, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "live_workspace_reconnect" } }
    const terminalInput: LiveEvent = { seq: 4, ts: 1, type: "human.action", actor: "human", data: { action: "terminal.input", bytes: 1 } }
    const edit: LiveEvent = { seq: 5, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "edit_file", path: "/workspace/src/app.ts" } }
    const job: LiveEvent = { seq: 6, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "job_start", name: "tests" } }
    const shellStarted: LiveEvent = { seq: 7, ts: 1, type: "tool.started", actor: "agent", data: { tool: "shell_start", call_id: "shell-1" } }
    const shellReady: LiveEvent = { seq: 8, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "shell_start", call_id: "shell-1", session_id: "session-1" } }

    expect(isOperationalActivityEvent(opened)).toBeFalse()
    expect(isOperationalActivityEvent(bootstrap)).toBeFalse()
    expect(isOperationalActivityEvent(reconnect)).toBeFalse()
    expect(isOperationalActivityEvent(terminalInput)).toBeFalse()
    expect(isOperationalActivityEvent(edit)).toBeTrue()
    expect(activityIntent(edit)).toBe("Editing app.ts")
    expect(activityDestination(edit)).toBe("files")
    expect(activityIntent(job)).toBe("Starting tests")
    expect(activityDestination(job)).toBe("jobs")
    expect(activityDestination(shellStarted)).toBe("detail")
    expect(activityDestination(shellReady)).toBe("terminal")
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
