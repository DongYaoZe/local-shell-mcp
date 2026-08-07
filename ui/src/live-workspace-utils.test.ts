import { describe, expect, test } from "bun:test"
import {
  controlDescription,
  controlLabel,
  eventDetail,
  eventTitle,
  formatBytes,
  joinPath,
  parentPath,
  renderDiffHtml,
  truncateContext,
  type LiveEvent,
} from "./live-workspace-utils"

describe("live workspace utilities", () => {
  test("control labels explain ownership", () => {
    expect(controlLabel("agent")).toBe("Observe")
    expect(controlLabel("shared")).toBe("Collaborate")
    expect(controlLabel("human")).toBe("Take over")
    expect(controlDescription("human")).toContain("ChatGPT remains read-only")
  })

  test("paths work for POSIX and Windows", () => {
    expect(parentPath("/workspace/src/file.py")).toBe("/workspace/src")
    expect(parentPath("file.py")).toBe(".")
    expect(parentPath("C:\\work\\src\\file.py")).toBe("C:\\work\\src")
    expect(parentPath("C:\\work")).toBe("C:\\")
    expect(parentPath("C:\\")).toBe("C:\\")
    expect(parentPath("C:/work")).toBe("C:/")
    expect(parentPath("C:/")).toBe("C:/")
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
    expect(eventDetail(event)).toContain("/workspace")
    expect(eventDetail(event)).toContain("1.4 s")
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
})
