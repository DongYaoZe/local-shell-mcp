export type ControlMode = "agent" | "shared" | "human"
export type DisplayMode = "inline" | "fullscreen" | "pip"

export type LiveEvent = {
  seq: number
  ts: number
  type: string
  actor: string
  data: Record<string, unknown>
}

type JsonRecord = Record<string, unknown>

function jsonRecord(value: unknown): JsonRecord | null {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return null
  return value as JsonRecord
}

export function toolResultFromOpenAiGlobals(globals: unknown): JsonRecord | null {
  const openai = jsonRecord(globals)
  if (!openai) return null

  const metadata = jsonRecord(openai.toolResponseMetadata)
  if (!metadata) return null

  const envelope = jsonRecord(metadata.mcp_tool_result) || jsonRecord(metadata.call_tool_result)
  if (!envelope) return null

  if (jsonRecord(envelope.structuredContent)) return envelope

  const structuredContent = jsonRecord(openai.toolOutput)
  return structuredContent ? { ...envelope, structuredContent } : envelope
}

export function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

export function formatClock(timestamp: number): string {
  if (!Number.isFinite(timestamp)) return "—"
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp * 1000))
}

export function formatDuration(milliseconds: unknown): string {
  const value = Number(milliseconds)
  if (!Number.isFinite(value) || value < 0) return ""
  if (value < 1000) return `${Math.round(value)} ms`
  if (value < 60_000) return `${(value / 1000).toFixed(value < 10_000 ? 1 : 0)} s`
  return `${Math.floor(value / 60_000)}m ${Math.round((value % 60_000) / 1000)}s`
}

export function formatBytes(bytes: unknown): string {
  const value = Number(bytes)
  if (!Number.isFinite(value) || value < 0) return "—"
  if (value < 1024) return `${value} B`
  const units = ["KiB", "MiB", "GiB", "TiB"]
  let size = value / 1024
  let unit = units[0]
  for (let index = 1; size >= 1024 && index < units.length; index += 1) {
    size /= 1024
    unit = units[index]
  }
  return `${size >= 10 ? size.toFixed(0) : size.toFixed(1)} ${unit}`
}

export function parentPath(path: string): string {
  if (!path || path === ".") return "."
  const driveRoot = path.match(/^([A-Za-z]:)([\\/]+)$/)
  if (driveRoot) return `${driveRoot[1]}${driveRoot[2][0]}`
  const uncShareRoot = /^(?:\\\\|\/\/)[^\\/]+[\\/][^\\/]+[\\/]?$/
  if (uncShareRoot.test(path)) return path
  const windows = path.includes("\\") && !path.includes("/")
  const separator = windows ? "\\" : "/"
  const normalized = path.replace(/[\\/]+$/, "")
  if (!normalized) return separator
  const index = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"))
  if (index < 0) return "."
  if (index === 0) return separator
  if (index === 2 && normalized[1] === ":") return `${normalized.slice(0, 2)}${separator}`
  return normalized.slice(0, index)
}

export function basename(path: string): string {
  const normalized = path.replace(/[\\/]+$/, "")
  const index = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"))
  return normalized.slice(index + 1) || normalized || "."
}

export function joinPath(parent: string, child: string): string {
  if (!parent || parent === ".") return child
  const separator = parent.includes("\\") && !parent.includes("/") ? "\\" : "/"
  if (parent === "/") return `/${child}`
  return `${parent.replace(/[\\/]+$/, "")}${separator}${child}`
}

export function controlLabel(mode: ControlMode): string {
  if (mode === "shared") return "Collaborate"
  if (mode === "human") return "Take over"
  return "Observe"
}

export function nextDisplayMode(current: DisplayMode, requested: Exclude<DisplayMode, "inline">): DisplayMode {
  return current === requested ? "inline" : requested
}

export function eventTitle(event: LiveEvent): string {
  const tool = String(event.data.tool ?? "")
  const action = String(event.data.action ?? "")
  if (event.type === "tool.started") return tool ? `Running ${tool}` : "Tool started"
  if (event.type === "tool.completed") return tool ? `${tool} completed` : "Tool completed"
  if (event.type === "tool.failed") return tool ? `${tool} failed` : "Tool failed"
  if (event.type === "tool.blocked") return tool ? `${tool} blocked by takeover` : "Tool blocked"
  if (event.type === "control.changed") return `Control → ${controlLabel(String(event.data.control) as ControlMode)}`
  if (event.type === "workspace.opened") return "Live workspace connected"
  if (event.type === "human.inspected_diff") return "Human inspected diff"
  if (event.type === "human.action") return action ? `Human: ${action}` : "Human action"
  return event.type.replaceAll(".", " ")
}

export function eventDetail(event: LiveEvent): string {
  const data = event.data
  const pieces: string[] = []
  for (const key of ["machine", "path", "cwd", "session_id", "job_id"] as const) {
    const value = data[key]
    if (value !== undefined && value !== null && value !== "") pieces.push(String(value))
  }
  if (typeof data.command === "string" && data.command) pieces.push(data.command)
  if (typeof data.error === "string" && data.error) pieces.push(data.error)
  const duration = formatDuration(data.duration_ms)
  if (duration) pieces.push(duration)
  return pieces.join(" · ")
}

export function eventTone(event: LiveEvent): "success" | "danger" | "warning" | "info" | "muted" {
  if (event.type === "tool.failed") return "danger"
  if (event.type === "tool.blocked") return "warning"
  if (event.type === "tool.completed") return "success"
  if (event.type === "tool.started") return "info"
  if (event.type === "human.action") return "info"
  return "muted"
}

export function renderDiffHtml(diff: string): string {
  if (!diff.trim()) return '<div class="empty-state">Working tree is clean.</div>'
  return diff.split("\n").map((line) => {
    let kind = "context"
    if (line.startsWith("diff --git") || line.startsWith("index ")) kind = "meta"
    else if (line.startsWith("@@")) kind = "hunk"
    else if (line.startsWith("+") && !line.startsWith("+++")) kind = "added"
    else if (line.startsWith("-") && !line.startsWith("---")) kind = "removed"
    return `<div class="diff-line ${kind}"><span>${escapeHtml(line || " ")}</span></div>`
  }).join("")
}

export function truncateContext(value: string, maxChars = 24_000): string {
  if (value.length <= maxChars) return value
  return `${value.slice(0, maxChars)}\n… [truncated by Live Workspace]`
}
