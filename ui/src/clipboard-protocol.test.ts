import { describe, expect, test } from "bun:test"
import {
  parseWebClipboardPayload,
  webClipboardClearSequence,
  webClipboardSequence,
} from "./clipboard-protocol"

describe("web clipboard protocol", () => {
  test("round-trips shell commands without exposing control characters", () => {
    const command = "curl -fsSL https://example.test/join | bash -s -- --name 测试节点"
    const sequence = webClipboardSequence(command)
    const payload = sequence.slice(sequence.indexOf(";") + 1, -1)

    expect(sequence).toStartWith("\u001b]777;")
    expect(sequence).toEndWith("\u0007")
    expect(parseWebClipboardPayload(payload)).toEqual({ type: "set", value: command })
  })

  test("clears a previously published command", () => {
    const sequence = webClipboardClearSequence()
    const payload = sequence.slice(sequence.indexOf(";") + 1, -1)

    expect(parseWebClipboardPayload(payload)).toEqual({ type: "clear" })
  })

  test("ignores unrelated and malformed payloads", () => {
    expect(parseWebClipboardPayload("other;clipboard;value")).toBeNull()
    expect(parseWebClipboardPayload("local-shell-mcp;clipboard;set;%E0%A4%A")).toBeNull()
  })
})
