import { describe, expect, test } from "bun:test"
import { parseWebClipboardPayload, webClipboardSequence } from "./clipboard-protocol"

describe("web clipboard protocol", () => {
  test("round-trips shell commands without exposing control characters", () => {
    const command = "curl -fsSL https://example.test/join | bash -s -- --name 测试节点"
    const sequence = webClipboardSequence(command)
    const payload = sequence.slice(sequence.indexOf(";") + 1, -1)

    expect(sequence).toStartWith("\u001b]777;")
    expect(sequence).toEndWith("\u0007")
    expect(parseWebClipboardPayload(payload)).toBe(command)
  })

  test("ignores unrelated and malformed payloads", () => {
    expect(parseWebClipboardPayload("other;clipboard;value")).toBeNull()
    expect(parseWebClipboardPayload("local-shell-mcp;clipboard;%E0%A4%A")).toBeNull()
  })
})
