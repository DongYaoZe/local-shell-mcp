import { describe, expect, test } from "bun:test"
import { fileBreadcrumbRows } from "./files"

describe("Native WebUI file breadcrumbs", () => {
  test("preserves Windows UNC share roots", () => {
    expect(fileBreadcrumbRows("\\\\server\\share\\dir\\file")).toEqual([
      { label: "\\\\server\\share", path: "\\\\server\\share" },
      { label: "dir", path: "\\\\server\\share\\dir" },
      { label: "file", path: "\\\\server\\share\\dir\\file" },
    ])
  })

  test("preserves drive and POSIX roots", () => {
    expect(fileBreadcrumbRows("C:\\work\\repo")[0]).toEqual({ label: "C:", path: "C:\\" })
    expect(fileBreadcrumbRows("/srv/app")[0]).toEqual({ label: "/", path: "/" })
  })
})
