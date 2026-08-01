import { describe, expect, test } from "bun:test"
import { TerminalWriteBuffer, type TerminalWriteChunk } from "./terminal-write-buffer"

describe("TerminalWriteBuffer", () => {
  test("preserves output order while a browser selection is active", () => {
    const writes: TerminalWriteChunk[] = []
    const buffer = new TerminalWriteBuffer((chunk) => writes.push(chunk))

    buffer.write("before")
    buffer.setHeld(true)
    buffer.write("first")
    buffer.write(new Uint8Array([1, 2, 3]))
    expect(writes).toEqual(["before"])

    buffer.setHeld(false)
    expect(writes[1]).toBe("first")
    expect(Array.from(writes[2] as Uint8Array)).toEqual([1, 2, 3])
  })

  test("can discard stale buffered output when reconnecting", () => {
    const writes: TerminalWriteChunk[] = []
    const buffer = new TerminalWriteBuffer((chunk) => writes.push(chunk))

    buffer.setHeld(true)
    buffer.write("stale")
    buffer.clear()
    buffer.setHeld(false)

    expect(writes).toEqual([])
  })

  test("releases a selection hold before buffered output can grow without bound", () => {
    const writes: TerminalWriteChunk[] = []
    let overflows = 0
    const buffer = new TerminalWriteBuffer((chunk) => writes.push(chunk), {
      maxPendingBytes: 8,
      onOverflow: () => { overflows += 1 },
    })

    buffer.setHeld(true)
    buffer.write("1234")
    expect(writes).toEqual([])
    buffer.write("5")

    expect(overflows).toBe(1)
    expect(writes).toEqual(["1234", "5"])
    buffer.write("live")
    expect(writes).toEqual(["1234", "5", "live"])
  })
})
