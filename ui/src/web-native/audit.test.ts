import { describe, expect, test } from "bun:test"
import type { AuditEntry, AuditPayload } from "../types"
import type { NativePageContext } from "./common"
import { AuditController } from "./audit"

describe("Native WebUI audit refresh", () => {
  test("keeps following the first row when new audit entries arrive", async () => {
    let resolvePayload!: (payload: AuditPayload) => void
    const context: NativePageContext = {
      api: {
        get: async () => new Promise<AuditPayload>((resolve) => { resolvePayload = resolve }) as never,
        send: async () => undefined as never,
      },
      uiPath: "/ui",
      accessToken: () => null,
      machines: () => [],
      notify: () => undefined,
      refreshChrome: async () => undefined,
    }
    const controller = new AuditController(context) as unknown as {
      entries: AuditEntry[]
      selected: number
      renderList: () => void
      loadDetail: () => Promise<void>
      refresh: () => Promise<void>
    }
    controller.entries = [{ id: "old-a", ts: 1, node: "local", operation: "tool", event: "a" }]
    controller.selected = 0
    controller.renderList = () => undefined
    controller.loadDetail = async () => undefined

    const refresh = controller.refresh()
    resolvePayload({
      count: 2,
      total_matched: 2,
      entries: [
        { id: "new-b", ts: 2, node: "local", operation: "tool", event: "b" },
        { id: "old-a", ts: 1, node: "local", operation: "tool", event: "a" },
      ],
    })
    await refresh

    expect(controller.selected).toBe(0)
    expect(controller.entries[controller.selected]?.id).toBe("new-b")
  })

  test("preserves a selection changed while refresh is pending", async () => {
    let resolvePayload!: (payload: AuditPayload) => void
    const context: NativePageContext = {
      api: {
        get: async () => new Promise<AuditPayload>((resolve) => { resolvePayload = resolve }) as never,
        send: async () => undefined as never,
      },
      uiPath: "/ui",
      accessToken: () => null,
      machines: () => [],
      notify: () => undefined,
      refreshChrome: async () => undefined,
    }
    const controller = new AuditController(context) as unknown as {
      entries: AuditEntry[]
      selected: number
      renderList: () => void
      loadDetail: () => Promise<void>
      refresh: () => Promise<void>
    }
    controller.entries = [
      { id: "old-a", ts: 1, node: "local", operation: "tool", event: "a" },
      { id: "old-b", ts: 2, node: "local", operation: "tool", event: "b" },
    ]
    controller.selected = 0
    controller.renderList = () => undefined
    controller.loadDetail = async () => undefined

    const refresh = controller.refresh()
    controller.selected = 1
    resolvePayload({
      count: 2,
      total_matched: 2,
      entries: [
        { id: "old-b", ts: 3, node: "local", operation: "tool", event: "b" },
        { id: "old-a", ts: 4, node: "local", operation: "tool", event: "a" },
      ],
    })
    await refresh

    expect(controller.selected).toBe(0)
    expect(controller.entries[controller.selected]?.id).toBe("old-b")
  })

  test("drops stale detail immediately when the selection changes", async () => {
    let resolveDetail!: (entry: AuditEntry) => void
    const context: NativePageContext = {
      api: {
        get: async () => new Promise<AuditEntry>((resolve) => { resolveDetail = resolve }) as never,
        send: async () => undefined as never,
      },
      uiPath: "/ui",
      accessToken: () => null,
      machines: () => [],
      notify: () => undefined,
      refreshChrome: async () => undefined,
    }
    const controller = new AuditController(context) as unknown as {
      entries: AuditEntry[]
      selected: number
      detail: AuditEntry | null
      renderDetail: () => void
      loadDetail: () => Promise<void>
    }
    controller.entries = [
      { id: "a", ts: 1, node: "local", operation: "tool", event: "a" },
      { id: "b", ts: 2, node: "local", operation: "tool", event: "b" },
    ]
    controller.selected = 1
    controller.detail = { id: "a", ts: 1, node: "local", operation: "tool", event: "a", output: "old" }
    let renders = 0
    controller.renderDetail = () => { renders += 1 }

    const loading = controller.loadDetail()
    expect(controller.detail).toBeNull()
    expect(renders).toBe(1)

    resolveDetail({ id: "b", ts: 2, node: "local", operation: "tool", event: "b", output: "new" })
    await loading
    expect(controller.detail?.id).toBe("b")
    expect(renders).toBe(2)
  })
})
