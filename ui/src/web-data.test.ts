import { describe, expect, test } from "bun:test"

import { visibleWorkloadCount } from "./web-data"

describe("native WebUI data mapping", () => {
  test("counts visible jobs and standalone sessions without double-counting job sessions", () => {
    expect(visibleWorkloadCount({ jobs: [{}], sessions: [{}] })).toBe(2)
  })

})
