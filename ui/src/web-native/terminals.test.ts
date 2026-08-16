import { describe, expect, test } from "bun:test"
import { TerminalsController } from "./terminals"

describe("Native WebUI terminal scrolling", () => {
  test("leaves wheel input to mouse-aware terminal applications", () => {
    let prevented = false
    let stopped = false
    let synced = false
    const controller = {
      scrollbackSupported: true,
      terminal: { modes: { mouseTrackingMode: "vt200" } },
      queueScrollbackSync: () => { synced = true },
    }
    const event = {
      deltaY: -120,
      preventDefault: () => { prevented = true },
      stopPropagation: () => { stopped = true },
    }

    ;(TerminalsController.prototype as any).onTerminalWheel.call(controller, event)

    expect(prevented).toBe(false)
    expect(stopped).toBe(false)
    expect(synced).toBe(true)
  })

  test("uses tmux scrollback for ordinary shell wheel input", () => {
    let prevented = false
    let stopped = false
    const scrollbar = { scrollTop: 40 }
    const controller = {
      scrollbackSupported: true,
      terminal: { modes: { mouseTrackingMode: "none" } },
      root: { querySelector: () => scrollbar },
    }
    const event = {
      deltaY: -120,
      preventDefault: () => { prevented = true },
      stopPropagation: () => { stopped = true },
    }

    ;(TerminalsController.prototype as any).onTerminalWheel.call(controller, event)

    expect(prevented).toBe(true)
    expect(stopped).toBe(true)
    expect(scrollbar.scrollTop).toBe(35)
  })

  test("operates tmux scrollback from the keyboard", () => {
    let prevented = false
    let stopped = false
    let requested = -1
    const controller = {
      scrollbackSupported: true,
      scrollbackHistory: 100,
      scrollbackPosition: 10,
      terminal: { rows: 20 },
      renderScrollbar: () => {},
      queueScrollRequest: (position: number) => { requested = position },
    }
    const event = {
      key: "PageUp",
      preventDefault: () => { prevented = true },
      stopPropagation: () => { stopped = true },
    }

    ;(TerminalsController.prototype as any).onScrollbarKeyDown.call(controller, event)

    expect(prevented).toBe(true)
    expect(stopped).toBe(true)
    expect(controller.scrollbackPosition).toBe(30)
    expect(requested).toBe(30)
  })
})
