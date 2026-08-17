import { describe, expect, test } from "bun:test"
import {
  activityDestination,
  activityEventKey,
  activityIntent,
  captureReverseFeedScrollState,
  coalesceActivityEvents,
  continuationDispatchStillValid,
  continuationCountdownState,
  eventDetail,
  eventTitle,
  formatBytes,
  formatCountdown,
  isOperationalActivityEvent,
  joinPath,
  mergeActivityEvents,
  parentPath,
  renderDiffHtml,
  restoreReverseFeedScrollTop,
  toggleWorkspaceDisplayMode,
  reconnectDelayMs,
  toolResultFromOpenAiGlobals,
  truncateContext,
  type LiveEvent,
} from "./live-workspace-utils"

describe("live workspace utilities", () => {
  test("activity rerenders keep the newest edge pinned but preserve historical reading position", () => {
    const following = captureReverseFeedScrollState(0, 1_000, 300)
    expect(restoreReverseFeedScrollTop(following, 1_120, 300)).toBe(0)

    const readingHistory = captureReverseFeedScrollState(240, 1_000, 300)
    expect(readingHistory.endGap).toBe(460)
    expect(restoreReverseFeedScrollTop(readingHistory, 1_120, 300)).toBe(360)

    const clamped = captureReverseFeedScrollState(900, 1_000, 300)
    expect(restoreReverseFeedScrollTop(clamped, 250, 300)).toBe(0)
  })

  test("Activity owns wheel scrolling inside embedded workspace panes", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain('root.addEventListener("wheel", onRootWheel, { passive: false })')
    expect(source).toContain('target.closest<HTMLElement>(".session-timeline")')
    expect(source).toContain('target.closest<HTMLElement>(".task-overview-column")')
    expect(source).toContain("event.preventDefault()")
    expect(source).toContain("event.stopPropagation()")
  })

  test("Live Workspace teardown does not recursively call its rendering tool", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain("app.onteardown = async")
    expect(source).toContain('name: "live_workspace_reconnect"')
    expect(source).not.toContain('name: "workspace_open"')
  })

  test("Live Workspace clears live-only activity when the Logical Session changes", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain("function resetActivityForSessionBoundary(): void")
    expect(source).toContain('continuationClaimId = ""')
    expect(source).toContain("resetActivityForSessionBoundary()")
    expect(source).toContain("applyLogicalSessionId(payload.session_id)")
    expect(source).toContain("const sessionChanged = !config || config.sessionId !== nextConfig.sessionId")
  })

  test("continuation claims reuse a client claim id across transient claim failures", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain('let continuationClaimId = ""')
    expect(source).toContain("continuationClaimId || `c_${crypto.randomUUID()")
    expect(source).toContain('JSON.stringify({ action: "claim", claim_id: requestedClaimId })')
  })

  test("continuation dispatch fails closed when revalidation errors", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain("Continuation could not be revalidated before host dispatch completed")
    expect(source).toContain("abortContinuationDispatch(")
  })

  test("display mode toggles only between floating and fullscreen", () => {
    expect(toggleWorkspaceDisplayMode("pip")).toBe("fullscreen")
    expect(toggleWorkspaceDisplayMode("fullscreen")).toBe("pip")
  })

  test("Live Workspace stays PiP/fullscreen-only and expands only after the live snapshot renders", async () => {
    const source = await Bun.file(new URL("./live-workspace.ts", import.meta.url)).text()
    expect(source).toContain('{ availableDisplayModes: ["pip", "fullscreen"] }')
    expect(source).not.toContain('availableDisplayModes: ["inline"')

    const snapshotStart = source.indexOf("async function loadSnapshot")
    const snapshotEnd = source.indexOf("async function pollEvents", snapshotStart)
    const snapshotSource = source.slice(snapshotStart, snapshotEnd)
    expect(snapshotSource.indexOf("renderCurrentTab()")).toBeLessThan(snapshotSource.indexOf("void enterPreferredDisplayModeAfterPaint(generation)"))

    const startupStart = source.indexOf("await app.connect()")
    const startupEnd = source.indexOf("passiveRefreshTimer = window.setInterval", startupStart)
    const chatGptStartup = source.slice(startupStart, startupEnd)
    expect(chatGptStartup).not.toContain("await enterPreferredDisplayMode()")
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

  test("continuation dispatch invalidates on plan changes or newer agent activity", () => {
    const plan = {
      status: "active",
      continuation_pending: true,
      continuation_claim_id: "c_1",
      last_agent_activity: 1_000,
    }
    expect(continuationDispatchStillValid(plan, "c_1", 1_000)).toBeTrue()
    expect(continuationDispatchStillValid({ ...plan, status: "blocked" }, "c_1", 1_000)).toBeFalse()
    expect(continuationDispatchStillValid({ ...plan, continuation_pending: false }, "c_1", 1_000)).toBeFalse()
    expect(continuationDispatchStillValid({ ...plan, continuation_claim_id: "c_2" }, "c_1", 1_000)).toBeFalse()
    expect(continuationDispatchStillValid({ ...plan, last_agent_activity: 1_001 }, "c_1", 1_000)).toBeFalse()
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

  test("activity lifecycle events coalesce into one stable tool row", () => {
    const started: LiveEvent = {
      seq: 40,
      ts: 1,
      type: "tool.started",
      actor: "agent",
      data: { tool: "run_shell", call_id: "call-1", cwd: "/workspace" },
    }
    const completed: LiveEvent = {
      seq: 41,
      ts: 2,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell", call_id: "call-1", duration_ms: 1000 },
    }

    const rows = coalesceActivityEvents([started, completed])
    expect(rows).toHaveLength(1)
    expect(rows[0]?.type).toBe("tool.completed")
    expect(rows[0]?.ts).toBe(1)
    expect(rows[0]?.data.cwd).toBe("/workspace")
    expect(rows[0]?.data.duration_ms).toBe(1000)
    expect(rows[0]?.data.started_at).toBe(1)
    expect(rows[0]?.data.finished_at).toBe(2)
    expect(activityEventKey(started)).toBe(activityEventKey(completed))
    expect(activityEventKey(rows[0]!)).toBe("call:call-1")
  })

  test("activity coalescing preserves rolling-window boundary completions", () => {
    const oldestCompletion: LiveEvent = {
      seq: 201,
      ts: 201,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "file_read", call_id: "aged-out-start", path: "/workspace/old.txt", duration_ms: 500 },
    }
    const started: LiveEvent = {
      seq: 202,
      ts: 202,
      type: "tool.started",
      actor: "agent",
      data: { tool: "run_shell", call_id: "paired", cwd: "/workspace" },
    }
    const completed: LiveEvent = {
      seq: 203,
      ts: 203,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell", call_id: "paired", duration_ms: 1000 },
    }
    const running: LiveEvent = {
      seq: 204,
      ts: 204,
      type: "tool.started",
      actor: "agent",
      data: { tool: "file_grep", call_id: "still-running" },
    }

    const rows = coalesceActivityEvents([oldestCompletion, started, completed, running])
    expect(rows).toHaveLength(3)
    expect(rows[0]).toEqual(oldestCompletion)
    expect(rows[1]?.type).toBe("tool.completed")
    expect(rows[1]?.data.call_id).toBe("paired")
    expect(rows[2]).toEqual(running)
  })

  test("activity summaries stay operational", () => {
    const event: LiveEvent = {
      seq: 4,
      ts: 1,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell", cwd: "/workspace", duration_ms: 1420 },
    }
    expect(eventTitle(event)).toBe("run_shell completed")
    expect(activityIntent(event)).toBe("Running command")
    expect(activityDestination(event)).toBe("detail")
    expect(eventDetail(event)).toContain("/workspace")
    expect(eventDetail(event)).toContain("1.4 s")
  })

  test("activity hides workspace bootstrap noise and routes useful operations", () => {
    const opened: LiveEvent = { seq: 1, ts: 1, type: "channel.opened", actor: "system", data: {} }
    const bootstrap: LiveEvent = { seq: 2, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "workspace_open" } }
    const reconnect: LiveEvent = { seq: 3, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "live_workspace_reconnect" } }
    const terminalInput: LiveEvent = { seq: 4, ts: 1, type: "human.action", actor: "human", data: { action: "terminal.input", bytes: 1 } }
    const edit: LiveEvent = { seq: 5, ts: 1, type: "tool.completed", actor: "agent", data: { tool: "file_edit", path: "/workspace/src/app.ts" } }
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

  test("activity keeps historical pre-v4 tool names usable", () => {
    const legacyShell: LiveEvent = {
      seq: 9,
      ts: 1,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "run_shell_tool", call_id: "legacy-shell" },
    }
    const legacyFile: LiveEvent = {
      seq: 10,
      ts: 1,
      type: "tool.completed",
      actor: "agent",
      data: { tool: "read_file", path: "/workspace/old.txt" },
    }

    expect(activityIntent(legacyShell)).toBe("Running command")
    expect(activityDestination(legacyShell)).toBe("detail")
    expect(activityIntent(legacyFile)).toBe("Reading old.txt")
    expect(activityDestination(legacyFile)).toBe("files")
  })

  test("activity merges durable tool events with live-only human events", () => {
    const durableStarted: LiveEvent = {
      seq: 1,
      ts: 10,
      type: "session.started",
      actor: "agent",
      data: { run_id: "run-1" },
    }
    const durableTool: LiveEvent = {
      seq: 2,
      ts: 12,
      type: "tool.completed",
      actor: "agent",
      data: { call_id: "call-1", tool: "file_write", path: "a.txt", durable: true },
    }
    const liveDuplicate: LiveEvent = {
      seq: 20,
      ts: 11.9,
      type: "tool.completed",
      actor: "agent",
      data: { call_id: "call-1", tool: "file_write", path: "a.txt" },
    }
    const humanDiff: LiveEvent = {
      seq: 21,
      ts: 13,
      type: "human.inspected_diff",
      actor: "human",
      data: { cwd: "." },
    }

    const merged = mergeActivityEvents(
      [durableStarted, durableTool],
      [liveDuplicate, humanDiff],
    )

    expect(merged).toHaveLength(3)
    expect(merged[0]).toEqual(durableStarted)
    expect(merged[1]).toEqual(durableTool)
    expect(merged[2]).toEqual(humanDiff)
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
