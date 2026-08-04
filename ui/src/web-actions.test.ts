import { describe, expect, test } from "bun:test"

const nativePages = ["files", "terminals", "remotes", "audit", "todos"] as const

describe("Native WebUI actions", () => {
  test("uses visible controls instead of shortcut footers", async () => {
    const sources = await Promise.all(
      nativePages.map((page) => Bun.file(new URL(`./web-native/${page}.ts`, import.meta.url)).text()),
    )

    expect(sources.join("\n")).not.toContain("shortcut-strip")
  })

  test("does not register document-wide single-key actions on ordinary WebUI pages", async () => {
    const sources = await Promise.all(
      ["files", "remotes", "audit", "todos"].map((page) => Bun.file(new URL(`./web-native/${page}.ts`, import.meta.url)).text()),
    )

    for (const source of sources) expect(source).not.toContain('this.listen(document, "keydown"')
  })

  test("exposes the previously shortcut-oriented operations as buttons", async () => {
    const files = await Bun.file(new URL("./web-native/files.ts", import.meta.url)).text()
    const audit = await Bun.file(new URL("./web-native/audit.ts", import.meta.url)).text()
    const terminals = await Bun.file(new URL("./web-native/terminals.ts", import.meta.url)).text()

    expect(files).toContain('"open"')
    expect(files).toContain('data-action="parent"')
    expect(audit).toContain('data-action="previous-record"')
    expect(audit).toContain('data-action="next-record"')
    expect(audit).toContain('button("Search", "search")')
    expect(terminals).toContain('"previous-session"')
    expect(terminals).toContain('"next-session"')
    for (const label of ["Copy", "Paste", "Find", "Clear", "Fullscreen"]) {
      expect(terminals).toContain(`button("${label}"`)
    }
  })
})
