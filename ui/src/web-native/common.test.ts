import { describe, expect, test } from "bun:test"
import { highlightedHtml } from "./common"

describe("Native WebUI syntax highlighting", () => {
  test("does not re-highlight generated span markup", () => {
    const rendered = highlightedHtml("// class remains a comment\nconst value = 'class'", "sample.ts")

    expect(rendered).toContain('<span class="syntax-comment">// class remains a comment</span>')
    expect(rendered).toContain('<span class="syntax-keyword">const</span>')
    expect(rendered).toContain('<span class="syntax-string">&#039;class&#039;</span>')
    expect(rendered).not.toContain('syntax-<span')
    expect(rendered.match(/syntax-keyword/g)?.length).toBe(1)
  })

  test("escapes source text before placing it in token spans", () => {
    const rendered = highlightedHtml('const html = "<script>"', "sample.js")

    expect(rendered).toContain('&lt;script&gt;')
    expect(rendered).not.toContain("<script>")
  })
})
