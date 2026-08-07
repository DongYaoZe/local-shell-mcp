import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
} from "@modelcontextprotocol/ext-apps"
import { FitAddon } from "@xterm/addon-fit"
import { Terminal } from "@xterm/xterm"
import {
  basename,
  controlDescription,
  controlLabel,
  escapeHtml,
  eventDetail,
  eventTitle,
  eventTone,
  formatBytes,
  formatClock,
  joinPath,
  parentPath,
  renderDiffHtml,
  truncateContext,
  type ControlMode,
  type LiveEvent,
} from "./live-workspace-utils"

type JsonRecord = Record<string, unknown>
type Machine = { name: string; status?: string; workdir?: string; version?: string; platform?: string }
type TerminalSession = { session_id: string; backend?: string; created?: number; attached?: number; cwd?: string; name?: string }
type FileEntry = { name: string; path: string; type: string; size?: number; modified?: number; hidden?: boolean }

type LiveConfig = {
  token: string
  apiBase: string
  uiPath: string
  workspaceId: string
  machine: string
  cwd: string
}

type Dashboard = {
  health?: string
  system?: JsonRecord
  machines?: { machines?: Machine[]; counts?: JsonRecord }
  jobs?: JsonRecord[]
  sessions?: JsonRecord[]
  session_count?: number
  activity?: JsonRecord[]
  alerts?: JsonRecord[]
  todo_counts?: JsonRecord
  version?: JsonRecord
}

const app = new App(
  { name: "local-shell-mcp-live-workspace", version: "1.0.0" },
  { availableDisplayModes: ["inline", "fullscreen", "pip"] },
)

const root = document.createElement("div")
root.id = "live-workspace-root"
document.body.append(root)

let config: LiveConfig | null = null
let control: ControlMode = "agent"
let events: LiveEvent[] = []
let cursor = 0
let pollGeneration = 0
let connected = false
let connectionMessage = "Waiting for Live Workspace…"
let activeTab = "activity"
let bootstrap: JsonRecord | null = null
let dashboard: Dashboard | null = null
let machines: Machine[] = []
let lastPassiveRefresh = 0
let passiveRefreshing = false

let terminal: Terminal | null = null
let fitAddon: FitAddon | null = null
let terminalSocket: WebSocket | null = null
let terminalResizeObserver: ResizeObserver | null = null
let terminalMachine = "local"
let terminalSessions: TerminalSession[] = []
let selectedSession = ""

let fileMachine = "local"
let filePath = "."
let fileEntries: FileEntry[] = []
let selectedFile = ""
let filePreview: JsonRecord | null = null
let fileEditing = false
let fileEditContent = ""
let fileEditSha = ""

let gitSnapshot: { machine?: string; cwd: string; status: JsonRecord; diff: JsonRecord } | null = null
let auditEntries: JsonRecord[] = []
let remoteSnapshot: JsonRecord | null = null

function icon(name: string): string {
  const paths: Record<string, string> = {
    activity: '<path d="M4 12h3l2-6 4 12 2-6h5"/>',
    terminal: '<path d="m5 7 4 4-4 4M11 15h7"/>',
    files: '<path d="M4 5h6l2 2h8v12H4z"/>',
    diff: '<path d="M7 4v16M4 7h6M14 8h6M17 5v6M14 17h6"/>',
    jobs: '<path d="M4 7h16v11H4zM8 7V4h8v3M8 12h8"/>',
    remotes: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    audit: '<path d="M5 3h14v18H5zM8 8h8M8 12h8M8 16h5"/>',
    expand: '<path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/>',
    pip: '<rect x="3" y="4" width="18" height="16" rx="2"/><rect x="11" y="11" width="7" height="5" rx="1"/>',
    refresh: '<path d="M20 6v5h-5M4 18v-5h5M18 9a7 7 0 0 0-12-2M6 15a7 7 0 0 0 12 2"/>',
    copy: '<rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
    chat: '<path d="M4 5h16v11H9l-5 4z"/>',
  }
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.activity}</svg>`
}

function shell(): void {
  root.innerHTML = `
    <div class="live-shell">
      <header class="topbar">
        <div class="brand-area">
          <div class="brand-mark">LS</div>
          <div class="brand-copy">
            <div class="title-row"><strong>Live Workspace</strong><span class="connection-dot" data-role="connection-dot"></span><span data-role="connection-label">${escapeHtml(connectionMessage)}</span></div>
            <div class="subtitle" data-role="subtitle">local-shell-mcp · real-time execution</div>
          </div>
        </div>
        <div class="top-actions">
          <div class="control-switch" role="group" aria-label="Execution control">
            ${controlButton("agent", "Observe")}${controlButton("shared", "Collaborate")}${controlButton("human", "Take over")}
          </div>
          <button class="icon-button" data-action="pip" title="Picture in picture">${icon("pip")}</button>
          <button class="icon-button" data-action="expand" title="Fullscreen">${icon("expand")}</button>
        </div>
      </header>
      <section class="status-strip">
        <div class="current-operation"><span class="pulse" data-role="op-pulse"></span><div><small>Current</small><strong data-role="current-op">No active tool call</strong><span data-role="current-detail">Waiting for activity</span></div></div>
        <div class="status-stat"><small>Control</small><strong data-role="control-label">${controlLabel(control)}</strong><span data-role="control-description">${controlDescription(control)}</span></div>
        <div class="status-stat compact-stat"><small>Machines</small><strong data-role="machine-count">—</strong><span data-role="machine-status">loading</span></div>
        <div class="status-stat compact-stat"><small>Workload</small><strong data-role="workload-count">—</strong><span data-role="workload-status">jobs + terminals</span></div>
      </section>
      <nav class="tabs" aria-label="Workspace views">
        ${tabButton("activity", "Activity")}${tabButton("terminal", "Terminal")}${tabButton("files", "Files")}${tabButton("diff", "Diff")}${tabButton("jobs", "Jobs")}${tabButton("remotes", "Remotes")}${tabButton("audit", "Audit")}
      </nav>
      <main class="workspace-main" data-role="main"><div class="loading"><span></span>${escapeHtml(connectionMessage)}</div></main>
      <div class="toast-stack" data-role="toasts" aria-live="polite"></div>
      <dialog class="live-dialog" data-role="dialog"><form method="dialog"><h3 data-role="dialog-title"></h3><p data-role="dialog-description"></p><label data-role="dialog-label"><span></span><input data-role="dialog-input"/></label><menu><button value="cancel">Cancel</button><button class="primary" value="confirm">Continue</button></menu></form></dialog>
    </div>`
  root.addEventListener("click", onRootClick)
  updateChrome()
}

function controlButton(mode: ControlMode, label: string): string {
  return `<button data-control="${mode}" class="${control === mode ? "active" : ""}">${label}</button>`
}

function tabButton(name: string, label: string): string {
  return `<button data-tab="${name}" class="${activeTab === name ? "active" : ""}">${icon(name)}<span>${label}</span></button>`
}

function qs<T extends Element>(selector: string): T | null {
  return root.querySelector<T>(selector)
}

function notify(message: string, tone: "info" | "success" | "warning" | "danger" = "info"): void {
  const host = qs<HTMLElement>("[data-role=toasts]")
  if (!host) return
  const item = document.createElement("div")
  item.className = `toast ${tone}`
  item.textContent = message
  host.append(item)
  setTimeout(() => item.classList.add("show"), 10)
  setTimeout(() => {
    item.classList.remove("show")
    setTimeout(() => item.remove(), 180)
  }, 3600)
}

async function promptValue(title: string, label: string, initial = "", description = ""): Promise<string | null> {
  const dialog = qs<HTMLDialogElement>("[data-role=dialog]")
  if (!dialog) return null
  const titleNode = dialog.querySelector<HTMLElement>("[data-role=dialog-title]")
  const descriptionNode = dialog.querySelector<HTMLElement>("[data-role=dialog-description]")
  const labelNode = dialog.querySelector<HTMLElement>("[data-role=dialog-label] span")
  const input = dialog.querySelector<HTMLInputElement>("[data-role=dialog-input]")
  if (!titleNode || !descriptionNode || !labelNode || !input) return null
  titleNode.textContent = title
  descriptionNode.textContent = description
  descriptionNode.hidden = !description
  labelNode.textContent = label
  input.value = initial
  return await new Promise((resolve) => {
    const close = () => {
      dialog.removeEventListener("close", close)
      resolve(dialog.returnValue === "confirm" ? input.value : null)
    }
    dialog.addEventListener("close", close)
    dialog.showModal()
    setTimeout(() => input.focus(), 0)
  })
}

function updateChrome(): void {
  qs<HTMLElement>("[data-role=connection-dot]")?.classList.toggle("connected", connected)
  const connectionLabel = qs<HTMLElement>("[data-role=connection-label]")
  if (connectionLabel) connectionLabel.textContent = connectionMessage
  root.querySelectorAll<HTMLButtonElement>("[data-control]").forEach((button) => {
    button.classList.toggle("active", button.dataset.control === control)
  })
  root.querySelectorAll<HTMLButtonElement>("[data-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === activeTab)
  })
  const controlNode = qs<HTMLElement>("[data-role=control-label]")
  if (controlNode) controlNode.textContent = controlLabel(control)
  const description = qs<HTMLElement>("[data-role=control-description]")
  if (description) description.textContent = controlDescription(control)

  const running = currentRunningEvent()
  const current = qs<HTMLElement>("[data-role=current-op]")
  const detail = qs<HTMLElement>("[data-role=current-detail]")
  const pulse = qs<HTMLElement>("[data-role=op-pulse]")
  if (current) current.textContent = running ? eventTitle(running) : "No active tool call"
  if (detail) detail.textContent = running ? eventDetail(running) || "In progress" : latestCompletedSummary()
  pulse?.classList.toggle("active", Boolean(running))

  const machineCount = qs<HTMLElement>("[data-role=machine-count]")
  if (machineCount) machineCount.textContent = machines.length ? String(machines.length) : "1"
  const online = machines.filter((item) => item.status === "online" || item.name === "local").length
  const machineStatus = qs<HTMLElement>("[data-role=machine-status]")
  if (machineStatus) machineStatus.textContent = `${online || 1} online`
  const workload = (dashboard?.jobs?.length || 0) + (dashboard?.session_count || dashboard?.sessions?.length || 0)
  const workloadCount = qs<HTMLElement>("[data-role=workload-count]")
  if (workloadCount) workloadCount.textContent = String(workload)

  if (terminal) terminal.options.disableStdin = control === "agent"
}

function currentRunningEvent(): LiveEvent | null {
  const completed = new Set(events.filter((event) => event.type === "tool.completed" || event.type === "tool.failed").map((event) => String(event.data.call_id || "")))
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (event.type === "tool.started" && !completed.has(String(event.data.call_id || ""))) return event
  }
  return null
}

function latestCompletedSummary(): string {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (["tool.completed", "tool.failed", "human.action"].includes(event.type)) return eventTitle(event)
  }
  return connected ? "Ready" : "Waiting for connection"
}

function onRootClick(event: MouseEvent): void {
  const target = (event.target as HTMLElement).closest<HTMLElement>("[data-tab],[data-control],[data-action]")
  if (!target) return
  if (target.dataset.tab) void switchTab(target.dataset.tab)
  if (target.dataset.control) void setControl(target.dataset.control as ControlMode)
  if (target.dataset.action) void handleAction(target.dataset.action, target)
}

async function handleAction(action: string, target: HTMLElement): Promise<void> {
  try {
    if (action === "expand") await requestDisplayMode("fullscreen")
    else if (action === "pip") await requestDisplayMode("pip")
    else if (action === "refresh") await refreshCurrent(true)
    else if (action === "activity-ask") await askAboutLatestActivity()
    else if (action === "terminal-new") await newTerminal()
    else if (action === "terminal-kill") await killTerminal()
    else if (action === "terminal-copy") await copyTerminal()
    else if (action === "terminal-ctrl-c") sendTerminal("\u0003")
    else if (action === "terminal-reconnect") connectTerminal()
    else if (action === "file-up") { filePath = parentPath(filePath); selectedFile = ""; await refreshFiles() }
    else if (action === "file-new") await createFile(false)
    else if (action === "file-new-dir") await createFile(true)
    else if (action === "file-delete") await deleteSelectedFile()
    else if (action === "file-edit") await beginFileEdit()
    else if (action === "file-save") await saveFileEdit()
    else if (action === "file-cancel-edit") { fileEditing = false; renderFiles() }
    else if (action === "file-context") await shareSelectedFile(false)
    else if (action === "file-ask") await shareSelectedFile(true)
    else if (action === "diff-context") await shareDiff(false)
    else if (action === "diff-ask") await shareDiff(true)
    else if (action === "remote-invite") await createRemoteInvite()
    else if (action === "remote-rename") await renameRemote(target.dataset.machine || "")
    else if (action === "remote-revoke") await revokeRemote(target.dataset.machine || "")
    else if (action === "audit-ask") await askAboutAudit(target.dataset.id || "")
  } catch (error) {
    notify(error instanceof Error ? error.message : String(error), "danger")
  }
}

async function requestDisplayMode(mode: "fullscreen" | "pip" | "inline"): Promise<void> {
  try {
    await app.requestDisplayMode({ mode })
  } catch (error) {
    notify(`Host did not change display mode: ${error instanceof Error ? error.message : String(error)}`, "warning")
  }
}

async function setControl(next: ControlMode): Promise<void> {
  if (!config || next === control) return
  const payload = await api<{ control: ControlMode }>("/api/live/control", {
    method: "POST",
    body: JSON.stringify({ control: next }),
  })
  control = payload.control
  updateChrome()
  renderCurrentTab()
  notify(`${controlLabel(control)} mode enabled`, control === "human" ? "warning" : "success")
}

async function switchTab(next: string): Promise<void> {
  if (next === activeTab) return
  if (activeTab === "terminal") destroyTerminal()
  activeTab = next
  updateChrome()
  renderCurrentTab()
  await refreshCurrent(false)
}

function mainNode(): HTMLElement {
  const node = qs<HTMLElement>("[data-role=main]")
  if (!node) throw new Error("Live Workspace root is unavailable")
  return node
}

function renderCurrentTab(): void {
  if (!config) {
    mainNode().innerHTML = `<div class="loading"><span></span>${escapeHtml(connectionMessage)}</div>`
    return
  }
  if (activeTab === "activity") renderActivity()
  else if (activeTab === "terminal") renderTerminal()
  else if (activeTab === "files") renderFiles()
  else if (activeTab === "diff") renderDiff()
  else if (activeTab === "jobs") renderJobs()
  else if (activeTab === "remotes") renderRemotes()
  else renderAudit()
}

function renderActivity(): void {
  const recent = [...events].reverse().slice(0, 120)
  const running = currentRunningEvent()
  const completed = events.filter((event) => event.type === "tool.completed").length
  const failed = events.filter((event) => event.type === "tool.failed").length
  const human = events.filter((event) => event.actor === "human").length
  mainNode().innerHTML = `
    <section class="view activity-view">
      <div class="view-toolbar"><div><h2>Operational activity</h2><p>Observable tool and human actions. Model private reasoning is never exposed.</p></div><div class="toolbar-actions"><button class="button" data-action="activity-ask">${icon("chat")}Ask about latest</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="metric-row">
        <div><small>Current</small><strong>${running ? escapeHtml(String(running.data.tool || "tool")) : "Idle"}</strong><span>${running ? escapeHtml(eventDetail(running) || "running") : "No active call"}</span></div>
        <div><small>Completed</small><strong>${completed}</strong><span>this workspace</span></div>
        <div><small>Failures</small><strong>${failed}</strong><span>${failed ? "needs attention" : "none"}</span></div>
        <div><small>Human actions</small><strong>${human}</strong><span>collaboration events</span></div>
      </div>
      <div class="panel activity-panel">
        <div class="panel-head"><strong>Timeline</strong><span>${recent.length} recent events</span></div>
        <div class="timeline">${recent.length ? recent.map(activityRow).join("") : '<div class="empty-state">No execution activity yet.</div>'}</div>
      </div>
    </section>`
}

function activityRow(event: LiveEvent): string {
  const detail = eventDetail(event)
  return `<div class="timeline-row ${eventTone(event)}"><div class="timeline-marker"><span></span></div><div class="timeline-copy"><div><strong>${escapeHtml(eventTitle(event))}</strong><span class="actor ${escapeHtml(event.actor)}">${escapeHtml(event.actor)}</span></div>${detail ? `<p>${escapeHtml(detail)}</p>` : ""}</div><time>${escapeHtml(formatClock(event.ts))}</time></div>`
}

async function askAboutLatestActivity(): Promise<void> {
  const recent = events.slice(-20)
  await app.updateModelContext({
    content: [{ type: "text", text: `Live Workspace recent operational activity:\n${recent.map((event) => `${formatClock(event.ts)} ${eventTitle(event)} — ${eventDetail(event)}`).join("\n")}` }],
    structuredContent: { liveWorkspaceEvents: recent },
  })
  await app.sendMessage({ role: "user", content: [{ type: "text", text: "Review the recent Live Workspace activity and tell me what matters, especially any failure, blocker, or next action." }] })
}

function renderTerminal(): void {
  const canWrite = control !== "agent"
  const session = terminalSessions.find((item) => item.session_id === selectedSession)
  mainNode().innerHTML = `
    <section class="view terminal-view">
      <div class="view-toolbar terminal-toolbar"><div class="toolbar-left"><label>Machine<select data-role="terminal-machine">${machineOptions(terminalMachine)}</select></label><label>Session<select data-role="terminal-session"><option value="">${terminalSessions.length ? "Select session" : "No sessions"}</option>${terminalSessions.map((item) => `<option value="${escapeHtml(item.session_id)}"${item.session_id === selectedSession ? " selected" : ""}>${escapeHtml(item.name || item.session_id)}</option>`).join("")}</select></label><span class="mode-pill ${control}">${canWrite ? "Interactive" : "Observe only"}</span></div><div class="toolbar-actions"><button class="button" data-action="terminal-new" ${canWrite ? "" : "disabled"}>New</button><button class="button" data-action="terminal-kill" ${canWrite && selectedSession ? "" : "disabled"}>Kill</button><button class="button" data-action="terminal-copy">${icon("copy")}Copy</button><button class="button" data-action="terminal-ctrl-c" ${canWrite && selectedSession ? "" : "disabled"}>Ctrl-C</button><button class="button" data-action="terminal-reconnect">Reconnect</button></div></div>
      <div class="terminal-card">
        <div class="terminal-title"><div><span class="terminal-led ${selectedSession ? "online" : ""}"></span><strong>${escapeHtml(session?.name || selectedSession || "Persistent terminal")}</strong><small>${escapeHtml(terminalMachine)}${session?.backend ? ` · ${escapeHtml(session.backend)}` : ""}</small></div><span>${canWrite ? "Human input enabled" : "Switch to Collaborate or Take over to type"}</span></div>
        <div class="terminal-host" data-role="terminal-host"></div>
        <form class="command-dock" data-role="command-form"><span>$</span><input data-role="command-input" autocomplete="off" placeholder="${canWrite ? "Send command to attached session" : "Observe mode — input disabled"}" ${canWrite && selectedSession ? "" : "disabled"}/><button ${canWrite && selectedSession ? "" : "disabled"}>Send</button></form>
      </div>
    </section>`
  wireTerminalControls()
  mountTerminal()
}

function machineOptions(selected: string): string {
  const rows = machines.length ? machines : [{ name: "local", status: "online" }]
  return rows.map((machine) => `<option value="${escapeHtml(machine.name)}"${machine.name === selected ? " selected" : ""}>${escapeHtml(machine.name)}${machine.status && machine.name !== "local" ? ` · ${escapeHtml(machine.status)}` : ""}</option>`).join("")
}

function wireTerminalControls(): void {
  const machineSelect = qs<HTMLSelectElement>("[data-role=terminal-machine]")
  const sessionSelect = qs<HTMLSelectElement>("[data-role=terminal-session]")
  machineSelect?.addEventListener("change", () => {
    terminalMachine = machineSelect.value
    selectedSession = ""
    void refreshTerminals()
  })
  sessionSelect?.addEventListener("change", () => {
    selectedSession = sessionSelect.value
    renderTerminal()
  })
  const form = qs<HTMLFormElement>("[data-role=command-form]")
  form?.addEventListener("submit", (event) => {
    event.preventDefault()
    const input = qs<HTMLInputElement>("[data-role=command-input]")
    if (!input || !input.value.trim()) return
    sendTerminal(`${input.value}\r`)
    input.value = ""
  })
}

function mountTerminal(): void {
  destroyTerminal()
  const host = qs<HTMLElement>("[data-role=terminal-host]")
  if (!host) return
  terminal = new Terminal({
    allowTransparency: true,
    cursorBlink: control !== "agent",
    cursorStyle: "bar",
    disableStdin: control === "agent",
    fontFamily: 'var(--font-mono, "SFMono-Regular", "Cascadia Code", Consolas, monospace)',
    fontSize: 13,
    lineHeight: 1.18,
    scrollback: 12_000,
    smoothScrollDuration: 60,
    theme: {
      background: "rgba(0,0,0,0)", foreground: "#d8e0ef", cursor: "#8f82ff", selectionBackground: "#65739180",
      black: "#101521", red: "#ff7b8b", green: "#71d6a1", yellow: "#e7b864", blue: "#79a7ff", magenta: "#bd9cff", cyan: "#65d5d0", white: "#e7ecf5",
      brightBlack: "#78849b", brightRed: "#ff9aa6", brightGreen: "#98e5b8", brightYellow: "#f1cd89", brightBlue: "#9ebeff", brightMagenta: "#d6bbff", brightCyan: "#8ee6e2", brightWhite: "#ffffff",
    },
  })
  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.open(host)
  terminal.onData((data) => sendTerminal(data))
  terminalResizeObserver = new ResizeObserver(() => requestAnimationFrame(() => fitTerminal()))
  terminalResizeObserver.observe(host)
  requestAnimationFrame(() => fitTerminal())
  if (selectedSession) connectTerminal()
  else terminal.write("\x1b[38;2;143;130;255mSelect or create a persistent session.\x1b[0m\r\n")
}

function fitTerminal(): void {
  if (!terminal || !fitAddon) return
  try { fitAddon.fit() } catch { return }
  if (terminalSocket?.readyState === WebSocket.OPEN) terminalSocket.send(JSON.stringify({ type: "resize", cols: terminal.cols, rows: terminal.rows }))
}

function destroyTerminal(): void {
  terminalSocket?.close()
  terminalSocket = null
  terminalResizeObserver?.disconnect()
  terminalResizeObserver = null
  terminal?.dispose()
  terminal = null
  fitAddon = null
}

function connectTerminal(): void {
  if (!config || !terminal || !selectedSession) return
  terminalSocket?.close()
  terminal.clear()
  terminal.write(`\x1b[38;2;143;130;255mAttaching to ${terminalMachine}:${selectedSession}…\x1b[0m\r\n`)
  const base = new URL(config.apiBase)
  const url = new URL(config.uiPath.replace(/\/$/, "") + "/ws/shell", base)
  url.protocol = base.protocol === "https:" ? "wss:" : "ws:"
  url.searchParams.set("machine", terminalMachine)
  url.searchParams.set("session_id", selectedSession)
  url.searchParams.set("cols", String(terminal.cols))
  url.searchParams.set("rows", String(terminal.rows))
  const socket = new WebSocket(url, ["lsm-ui", bearerProtocol(config.token)])
  socket.binaryType = "arraybuffer"
  terminalSocket = socket
  socket.onopen = () => {
    if (terminalSocket !== socket) return
    fitTerminal()
    notify(`Attached to ${selectedSession}`, "success")
  }
  socket.onmessage = async (event) => {
    if (terminalSocket !== socket || !terminal) return
    if (event.data instanceof ArrayBuffer) terminal.write(new Uint8Array(event.data))
    else if (event.data instanceof Blob) terminal.write(new Uint8Array(await event.data.arrayBuffer()))
    else terminal.write(String(event.data))
  }
  socket.onclose = (event) => {
    if (terminalSocket !== socket) return
    terminalSocket = null
    terminal?.write(`\r\n\x1b[38;2;231;184;100mDisconnected${event.reason ? `: ${event.reason}` : ""}.\x1b[0m\r\n`)
  }
}

function bearerProtocol(token: string): string {
  let binary = ""
  for (const byte of new TextEncoder().encode(token)) binary += String.fromCharCode(byte)
  return `bearer.${btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "")}`
}

function sendTerminal(data: string): void {
  if (control === "agent" || !selectedSession) return
  if (terminalSocket?.readyState === WebSocket.OPEN) terminalSocket.send(new TextEncoder().encode(data))
}

async function refreshTerminals(): Promise<void> {
  if (!config) return
  const requestMachine = terminalMachine
  const payload = await api<{ machine: string; sessions: TerminalSession[] }>(`/api/ui/terminals?machine=${encodeURIComponent(requestMachine)}`)
  if (terminalMachine !== requestMachine) return
  terminalSessions = payload.sessions || []
  if (!terminalSessions.some((item) => item.session_id === selectedSession)) selectedSession = terminalSessions[0]?.session_id || ""
  if (activeTab === "terminal") renderTerminal()
}

async function newTerminal(): Promise<void> {
  if (control === "agent") return
  const name = await promptValue("New terminal", "Optional name", "", `Create a persistent shell on ${terminalMachine}.`)
  if (name === null) return
  const result = await api<JsonRecord>("/api/ui/terminals/start", { method: "POST", body: JSON.stringify({ machine: terminalMachine, cwd: config?.cwd || ".", name: name || null }) })
  selectedSession = String(result.session_id || "")
  await refreshTerminals()
}

async function killTerminal(): Promise<void> {
  if (control === "agent" || !selectedSession) return
  await api("/api/ui/terminals/kill", { method: "POST", body: JSON.stringify({ machine: terminalMachine, session_id: selectedSession }) })
  selectedSession = ""
  await refreshTerminals()
}

async function copyTerminal(): Promise<void> {
  const text = terminal?.getSelection() || ""
  if (!text) { notify("Select terminal text first", "info"); return }
  await navigator.clipboard.writeText(text)
  notify("Terminal selection copied", "success")
}

function renderFiles(): void {
  const canWrite = control !== "agent"
  const selected = fileEntries.find((entry) => entry.path === selectedFile)
  mainNode().innerHTML = `
    <section class="view files-view">
      <div class="view-toolbar files-toolbar"><div class="path-controls"><label>Machine<select data-role="file-machine">${machineOptions(fileMachine)}</select></label><button class="button" data-action="file-up">Up</button><input data-role="file-path" value="${escapeHtml(filePath)}" aria-label="Path"/></div><div class="toolbar-actions"><button class="button" data-action="file-new" ${canWrite ? "" : "disabled"}>New file</button><button class="button" data-action="file-new-dir" ${canWrite ? "" : "disabled"}>New folder</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="files-grid">
        <section class="panel file-list-panel"><div class="panel-head"><strong>${escapeHtml(fileMachine)}:${escapeHtml(filePath)}</strong><span>${fileEntries.length} entries</span></div><div class="file-list">${fileEntries.length ? fileEntries.map(fileRow).join("") : '<div class="empty-state">Directory is empty.</div>'}</div></section>
        <section class="panel preview-panel"><div class="panel-head"><div><strong>${escapeHtml(selected?.name || "Preview")}</strong><span>${selected ? `${escapeHtml(selected.type)} · ${formatBytes(selected.size)}` : "Choose a file"}</span></div><div class="preview-actions">${selected?.type === "file" ? `<button class="text-button" data-action="file-context">Send context</button><button class="text-button" data-action="file-ask">Ask ChatGPT</button><button class="text-button" data-action="file-edit" ${canWrite ? "" : "disabled"}>Edit</button><button class="text-button danger" data-action="file-delete" ${canWrite ? "" : "disabled"}>Delete</button>` : ""}</div></div><div class="file-preview" data-role="file-preview">${renderFilePreview()}</div></section>
      </div>
    </section>`
  wireFileControls()
  if (filePreview?.kind === "image") requestAnimationFrame(drawFileImage)
}

function fileRow(entry: FileEntry): string {
  const selected = entry.path === selectedFile
  return `<button class="file-row ${selected ? "selected" : ""}" data-file="${escapeHtml(entry.path)}"><span class="file-icon ${entry.type}">${entry.type === "dir" ? "⌑" : "·"}</span><span><strong>${escapeHtml(entry.name)}</strong><small>${entry.type === "dir" ? "folder" : formatBytes(entry.size)}</small></span><time>${entry.modified ? new Date(entry.modified * 1000).toLocaleString() : ""}</time></button>`
}

function renderFilePreview(): string {
  if (fileEditing) {
    return `<div class="editor-wrap"><textarea data-role="file-editor" spellcheck="false">${escapeHtml(fileEditContent)}</textarea><div class="editor-actions"><span>Optimistic save checks the original SHA-256.</span><button class="button" data-action="file-cancel-edit">Cancel</button><button class="button primary" data-action="file-save">Save</button></div></div>`
  }
  if (!selectedFile) return '<div class="empty-state">Select a file or folder.</div>'
  if (!filePreview) return '<div class="loading small"><span></span>Loading preview…</div>'
  const kind = String(filePreview.kind || "")
  if (kind === "directory") return `<div class="empty-state">Open the folder to browse its contents.</div>`
  if (kind === "image") return '<div class="image-stage"><canvas data-role="file-image"></canvas><span>Image preview</span></div>'
  if (kind === "binary") return `<pre class="code-preview">${escapeHtml(String(filePreview.preview || "Binary file"))}</pre>`
  return `<pre class="code-preview">${escapeHtml(String(filePreview.content || ""))}</pre>`
}

function drawFileImage(): void {
  if (!filePreview || filePreview.kind !== "image") return
  const canvas = qs<HTMLCanvasElement>("[data-role=file-image]")
  const encoded = String(filePreview.rgba || "")
  const width = Number(filePreview.width || 0)
  const height = Number(filePreview.height || 0)
  if (!canvas || !encoded || !width || !height) return
  const raw = atob(encoded)
  const bytes = Uint8ClampedArray.from(raw, (char) => char.charCodeAt(0))
  canvas.width = width
  canvas.height = height
  canvas.getContext("2d")?.putImageData(new ImageData(bytes, width, height), 0, 0)
}

function wireFileControls(): void {
  const machine = qs<HTMLSelectElement>("[data-role=file-machine]")
  const path = qs<HTMLInputElement>("[data-role=file-path]")
  machine?.addEventListener("change", () => { fileMachine = machine.value; filePath = "."; selectedFile = ""; void refreshFiles() })
  path?.addEventListener("keydown", (event) => { if (event.key === "Enter") { filePath = path.value || "."; selectedFile = ""; void refreshFiles() } })
  root.querySelectorAll<HTMLButtonElement>("[data-file]").forEach((row) => {
    row.addEventListener("click", () => void selectFile(row.dataset.file || ""))
    row.addEventListener("dblclick", () => {
      const entry = fileEntries.find((item) => item.path === row.dataset.file)
      if (entry?.type === "dir") { filePath = entry.path; selectedFile = ""; void refreshFiles() }
    })
  })
}

async function selectFile(path: string): Promise<void> {
  selectedFile = path
  fileEditing = false
  filePreview = null
  renderFiles()
  const requestMachine = fileMachine
  const entry = fileEntries.find((item) => item.path === path)
  if (!entry) return
  const preview = entry.type === "dir"
    ? { kind: "directory" }
    : await api<JsonRecord>(`/api/ui/files/preview?machine=${encodeURIComponent(requestMachine)}&path=${encodeURIComponent(path)}&columns=120&rows=50`)
  if (selectedFile !== path || fileMachine !== requestMachine) return
  filePreview = preview
  if (activeTab === "files") renderFiles()
}

async function refreshFiles(): Promise<void> {
  const requestMachine = fileMachine
  const requestPath = filePath
  const payload = await api<{ entries: FileEntry[]; path: string; machine: string }>(`/api/ui/files?machine=${encodeURIComponent(requestMachine)}&path=${encodeURIComponent(requestPath)}`)
  if (fileMachine !== requestMachine || filePath !== requestPath) return
  fileEntries = payload.entries || []
  filePath = payload.path || filePath
  if (!fileEntries.some((item) => item.path === selectedFile)) selectedFile = ""
  filePreview = null
  fileEditing = false
  if (activeTab === "files") renderFiles()
}

async function createFile(directory: boolean): Promise<void> {
  if (control === "agent") return
  const name = await promptValue(directory ? "New folder" : "New file", "Name", "", `Create inside ${filePath}.`)
  if (!name?.trim()) return
  const path = joinPath(filePath, name.trim())
  await api(`/api/ui/files/${directory ? "mkdir" : "touch"}`, { method: "POST", body: JSON.stringify({ machine: fileMachine, path }) })
  selectedFile = path
  await refreshFiles()
}

async function deleteSelectedFile(): Promise<void> {
  if (control === "agent" || !selectedFile) return
  const entry = fileEntries.find((item) => item.path === selectedFile)
  const confirmation = await promptValue("Delete entry", `Type ${basename(selectedFile)} to confirm`, "", "This action cannot be undone by the Live Workspace.")
  if (confirmation !== basename(selectedFile)) return
  await api("/api/ui/files/delete", { method: "POST", body: JSON.stringify({ machine: fileMachine, path: selectedFile, recursive: entry?.type === "dir" }) })
  selectedFile = ""
  await refreshFiles()
}

async function beginFileEdit(): Promise<void> {
  if (control === "agent" || !selectedFile) return
  const requestMachine = fileMachine
  const requestPath = selectedFile
  const content = await api<JsonRecord>(`/api/ui/files/content?machine=${encodeURIComponent(requestMachine)}&path=${encodeURIComponent(requestPath)}`)
  if (fileMachine !== requestMachine || selectedFile !== requestPath) return
  fileEditContent = String(content.content || "")
  fileEditSha = String(content.sha256 || "")
  fileEditing = true
  renderFiles()
}

async function saveFileEdit(): Promise<void> {
  if (control === "agent" || !selectedFile) return
  const editor = qs<HTMLTextAreaElement>("[data-role=file-editor]")
  if (!editor) return
  await api("/api/ui/files/write", { method: "POST", body: JSON.stringify({ machine: fileMachine, path: selectedFile, content: editor.value, overwrite: true, expected_sha256: fileEditSha || null }) })
  fileEditing = false
  filePreview = null
  await selectFile(selectedFile)
  notify("File saved", "success")
}

async function shareSelectedFile(ask: boolean): Promise<void> {
  if (!selectedFile) return
  const requestMachine = fileMachine
  const requestPath = selectedFile
  const content = await api<JsonRecord>(`/api/ui/files/content?machine=${encodeURIComponent(requestMachine)}&path=${encodeURIComponent(requestPath)}`)
  if (fileMachine !== requestMachine || selectedFile !== requestPath) return
  const text = truncateContext(String(content.content || ""))
  await app.updateModelContext({ content: [{ type: "text", text: `Selected file ${requestMachine}:${requestPath}:\n\n${text}` }], structuredContent: { selectedFile: { machine: requestMachine, path: requestPath, sha256: content.sha256 } } })
  notify("Selected file added to model context", "success")
  if (ask) await app.sendMessage({ role: "user", content: [{ type: "text", text: `Inspect the selected file ${requestPath} in Live Workspace. Explain anything important and suggest or make the next appropriate change.` }] })
}

function renderDiff(): void {
  const status = gitSnapshot ? String(gitSnapshot.status.stdout || gitSnapshot.status.stderr || "") : ""
  const diff = gitSnapshot ? String(gitSnapshot.diff.stdout || gitSnapshot.diff.stderr || "") : ""
  mainNode().innerHTML = `
    <section class="view diff-view"><div class="view-toolbar"><div><h2>Working tree diff</h2><p>${escapeHtml(gitSnapshot?.machine || config?.machine || "local")}:${escapeHtml(config?.cwd || ".")} · unstaged and staged changes</p></div><div class="toolbar-actions"><button class="button" data-action="diff-context">Send context</button><button class="button" data-action="diff-ask">${icon("chat")}Ask for review</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="diff-layout"><section class="panel status-panel"><div class="panel-head"><strong>Git status</strong><span>${escapeHtml(gitSnapshot?.cwd || config?.cwd || ".")}</span></div><pre>${escapeHtml(status || "Clean")}</pre></section><section class="panel diff-panel"><div class="panel-head"><strong>Changes</strong><span>${diff ? `${diff.split("\n").length} lines` : "clean"}</span></div><div class="diff-code">${gitSnapshot ? renderDiffHtml(diff) : '<div class="loading small"><span></span>Loading diff…</div>'}</div></section></div>
    </section>`
}

async function refreshDiff(): Promise<void> {
  gitSnapshot = await api(`/api/live/git?machine=${encodeURIComponent(config?.machine || "local")}&cwd=${encodeURIComponent(config?.cwd || ".")}`)
  if (activeTab === "diff") renderDiff()
}

async function shareDiff(ask: boolean): Promise<void> {
  if (!gitSnapshot) await refreshDiff()
  const status = String(gitSnapshot?.status.stdout || "")
  const diff = truncateContext(String(gitSnapshot?.diff.stdout || ""), 28_000)
  await app.updateModelContext({ content: [{ type: "text", text: `Live Workspace git status (${gitSnapshot?.machine || config?.machine || "local"}):\n${status}\n\nDiff:\n${diff}` }], structuredContent: { git: { machine: gitSnapshot?.machine || config?.machine || "local", cwd: gitSnapshot?.cwd, status } } })
  notify("Diff added to model context", "success")
  if (ask) await app.sendMessage({ role: "user", content: [{ type: "text", text: "Review the current Live Workspace git diff. Identify correctness risks, regressions, missing tests, and concrete improvements. Make fixes when appropriate." }] })
}

function renderJobs(): void {
  const jobs = dashboard?.jobs || []
  const sessions = dashboard?.sessions || []
  mainNode().innerHTML = `
    <section class="view jobs-view"><div class="view-toolbar"><div><h2>Jobs & sessions</h2><p>Active managed work and persistent shells across the workspace.</p></div><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div>
      <div class="jobs-grid"><section class="panel"><div class="panel-head"><strong>Managed jobs</strong><span>${jobs.length} active</span></div><div class="object-list">${jobs.length ? jobs.map(jobRow).join("") : '<div class="empty-state">No active managed jobs.</div>'}</div></section><section class="panel"><div class="panel-head"><strong>Standalone terminals</strong><span>${sessions.length} visible</span></div><div class="object-list">${sessions.length ? sessions.map(sessionRow).join("") : '<div class="empty-state">No standalone persistent terminals.</div>'}</div></section></div>
    </section>`
}

function jobRow(job: JsonRecord): string {
  const status = String(job.status || "unknown")
  return `<div class="object-row"><span class="state-dot ${escapeHtml(status)}"></span><div><strong>${escapeHtml(String(job.name || job.job_id || "job"))}</strong><p>${escapeHtml(String(job.command || job.kind || ""))}</p></div><div class="object-meta"><span>${escapeHtml(status)}</span><small>${escapeHtml(String(job.machine || "local"))}</small></div></div>`
}

function sessionRow(session: JsonRecord): string {
  return `<button class="object-row clickable" data-open-session="${escapeHtml(String(session.session_id || ""))}"><span class="state-dot running"></span><div><strong>${escapeHtml(String(session.name || session.session_id || "terminal"))}</strong><p>${escapeHtml(String(session.backend || "persistent shell"))}</p></div><div class="object-meta"><span>${escapeHtml(String(session.machine || "local"))}</span><small>terminal</small></div></button>`
}

function wireJobRows(): void {
  root.querySelectorAll<HTMLButtonElement>("[data-open-session]").forEach((row) => {
    row.addEventListener("click", () => {
      selectedSession = row.dataset.openSession || ""
      terminalMachine = String((dashboard?.sessions || []).find((item) => item.session_id === selectedSession)?.machine || "local")
      void switchTab("terminal")
    })
  })
}

function renderRemotes(): void {
  const enabled = bootstrap ? Boolean((bootstrap.features as JsonRecord | undefined)?.remote) : true
  const rows = (remoteSnapshot?.machines as Machine[] | undefined) || []
  const canWrite = control !== "agent"
  mainNode().innerHTML = `
    <section class="view remotes-view"><div class="view-toolbar"><div><h2>Remote machines</h2><p>Worker connectivity, workdirs and administrative actions.</p></div><div class="toolbar-actions"><button class="button primary" data-action="remote-invite" ${enabled && canWrite ? "" : "disabled"}>Invite machine</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="panel remote-panel"><div class="panel-head"><strong>Machines</strong><span>${enabled ? `${rows.length} registered` : "remote support disabled"}</span></div><div class="remote-grid">${rows.length ? rows.map((machine) => remoteCard(machine, canWrite)).join("") : `<div class="empty-state">${enabled ? "No remote workers registered." : "Remote worker support is disabled."}</div>`}</div></div>
    </section>`
}

function remoteCard(machine: Machine, canWrite: boolean): string {
  return `<article class="remote-card"><div class="remote-head"><span class="machine-icon">${icon("remotes")}</span><div><strong>${escapeHtml(machine.name)}</strong><span class="status-chip ${machine.status === "online" ? "online" : "offline"}">${escapeHtml(machine.status || "unknown")}</span></div></div><dl><div><dt>Workdir</dt><dd>${escapeHtml(machine.workdir || "—")}</dd></div><div><dt>Version</dt><dd>${escapeHtml(machine.version || "—")}</dd></div><div><dt>Platform</dt><dd>${escapeHtml(machine.platform || "—")}</dd></div></dl><footer><button class="text-button" data-action="remote-rename" data-machine="${escapeHtml(machine.name)}" ${canWrite ? "" : "disabled"}>Rename</button><button class="text-button danger" data-action="remote-revoke" data-machine="${escapeHtml(machine.name)}" ${canWrite ? "" : "disabled"}>Revoke</button></footer></article>`
}

async function refreshRemotes(): Promise<void> {
  if (bootstrap && !(bootstrap.features as JsonRecord | undefined)?.remote) { remoteSnapshot = { machines: [] }; if (activeTab === "remotes") renderRemotes(); return }
  remoteSnapshot = await api<JsonRecord>("/api/ui/remotes")
  if (activeTab === "remotes") renderRemotes()
}

async function createRemoteInvite(): Promise<void> {
  if (control === "agent") return
  const name = await promptValue("Invite remote machine", "Machine name (optional)", "", "A one-time join command will be generated.")
  if (name === null) return
  const result = await api<JsonRecord>("/api/ui/remotes", { method: "POST", body: JSON.stringify({ name: name || null }) })
  const command = String(result.command || result.join_command || result.invite || "")
  if (command) {
    await navigator.clipboard.writeText(command)
    notify("Invite command copied to clipboard", "success")
  } else notify("Remote invitation created", "success")
  await refreshRemotes()
}

async function renameRemote(machine: string): Promise<void> {
  if (control === "agent" || !machine) return
  const name = await promptValue("Rename remote", "New name", machine)
  if (!name?.trim() || name === machine) return
  const newName = name.trim()
  await api("/api/ui/remotes/rename", { method: "POST", body: JSON.stringify({ machine, new_name: newName }) })
  if (config?.machine === machine) {
    config = { ...config, machine: newName }
    gitSnapshot = null
  }
  if (fileMachine === machine) {
    fileMachine = newName
    fileEntries = []
    selectedFile = ""
    filePreview = null
    fileEditing = false
  }
  if (terminalMachine === machine) {
    terminalMachine = newName
    terminalSessions = []
    selectedSession = ""
    terminalSocket?.close()
    terminalSocket = null
  }
  await refreshAllCore()
  await refreshRemotes()
}

async function revokeRemote(machine: string): Promise<void> {
  if (control === "agent" || !machine) return
  const confirmation = await promptValue("Revoke remote", `Type ${machine} to confirm`, "", "The worker will need a new invitation to reconnect.")
  if (confirmation !== machine) return
  await api("/api/ui/remotes/revoke", { method: "POST", body: JSON.stringify({ machine }) })
  await refreshAllCore()
  await refreshRemotes()
}

function renderAudit(): void {
  mainNode().innerHTML = `
    <section class="view audit-view"><div class="view-toolbar"><div><h2>Audit stream</h2><p>Structured MCP activity retained by local-shell-mcp.</p></div><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div>
      <div class="panel audit-panel"><div class="panel-head"><strong>Recent entries</strong><span>${auditEntries.length} loaded</span></div><div class="audit-table"><div class="audit-header"><span>Time</span><span>Operation</span><span>Node</span><span>Status</span><span></span></div>${auditEntries.length ? auditEntries.map(auditRow).join("") : '<div class="empty-state">No audit entries.</div>'}</div></div>
    </section>`
}

function auditRow(entry: JsonRecord): string {
  const ok = entry.ok
  const status = ok === false ? "failed" : String(entry.status || (ok === true ? "ok" : "recorded"))
  return `<div class="audit-row"><time>${escapeHtml(formatClock(Number(entry.ts || 0)))}</time><div><strong>${escapeHtml(String(entry.tool || entry.operation || entry.event || "event"))}</strong><small>${escapeHtml(String(entry.purpose || entry.command || ""))}</small></div><span>${escapeHtml(String(entry.node || entry.machine || "local"))}</span><span class="audit-status ${ok === false ? "danger" : ""}">${escapeHtml(status)}</span><button class="text-button" data-action="audit-ask" data-id="${escapeHtml(String(entry.id || ""))}">Ask</button></div>`
}

async function refreshAudit(): Promise<void> {
  const payload = await api<JsonRecord>("/api/ui/audit?limit=150&sort=desc")
  auditEntries = (payload.entries as JsonRecord[] | undefined) || []
  if (activeTab === "audit") renderAudit()
}

async function askAboutAudit(id: string): Promise<void> {
  const entry = auditEntries.find((item) => String(item.id || "") === id)
  if (!entry) return
  let detail: unknown = entry
  try { detail = await api(`/api/ui/audit/detail?id=${encodeURIComponent(id)}`) } catch { /* preview is enough */ }
  await app.updateModelContext({ content: [{ type: "text", text: `Selected local-shell-mcp audit entry:\n${truncateContext(JSON.stringify(detail, null, 2), 20_000)}` }], structuredContent: { auditEntryId: id } })
  await app.sendMessage({ role: "user", content: [{ type: "text", text: "Explain the selected Live Workspace audit entry, whether it indicates a problem, and what I should do next." }] })
}

async function refreshJobs(): Promise<void> {
  dashboard = await api<Dashboard>(`/api/ui/dashboard?machine=${encodeURIComponent(config?.machine || "local")}`)
  updateChrome()
  if (activeTab === "jobs") { renderJobs(); wireJobRows() }
}

async function refreshAllCore(): Promise<void> {
  if (!config || passiveRefreshing) return
  passiveRefreshing = true
  try {
    const [boot, dash] = await Promise.all([
      api<JsonRecord>("/api/ui/bootstrap"),
      api<Dashboard>(`/api/ui/dashboard?machine=${encodeURIComponent(config.machine || "local")}`),
    ])
    bootstrap = boot
    dashboard = dash
    const nested = boot.machines as JsonRecord | undefined
    machines = (nested?.machines as Machine[] | undefined) || []
    if (!machines.some((item) => item.name === terminalMachine)) terminalMachine = machines.some((item) => item.name === "local") ? "local" : machines[0]?.name || "local"
    if (!machines.some((item) => item.name === fileMachine)) fileMachine = terminalMachine
    lastPassiveRefresh = Date.now()
    updateChrome()
  } finally {
    passiveRefreshing = false
  }
}

async function refreshCurrent(force: boolean): Promise<void> {
  if (!config) return
  if (force || Date.now() - lastPassiveRefresh > 4_000) await refreshAllCore()
  if (activeTab === "terminal") await refreshTerminals()
  else if (activeTab === "files") await refreshFiles()
  else if (activeTab === "diff") await refreshDiff()
  else if (activeTab === "jobs") await refreshJobs()
  else if (activeTab === "remotes") await refreshRemotes()
  else if (activeTab === "audit") await refreshAudit()
  else renderActivity()
}

async function api<T = JsonRecord>(path: string, init: RequestInit = {}): Promise<T> {
  if (!config) throw new Error("Live Workspace is not connected")
  const url = new URL(path, config.apiBase.endsWith("/") ? config.apiBase : `${config.apiBase}/`)
  const headers = new Headers(init.headers)
  headers.set("Authorization", `Bearer ${config.token}`)
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json")
  const response = await fetch(url, { ...init, headers, credentials: "omit", cache: "no-store" })
  let payload: JsonRecord
  try { payload = await response.json() as JsonRecord } catch { throw new Error(`Live API returned HTTP ${response.status}`) }
  if (!response.ok || payload.ok === false) throw new Error(String(payload.message || payload.detail || `HTTP ${response.status}`))
  return (payload.data ?? payload) as T
}

function mergeEvents(incoming: LiveEvent[]): void {
  if (!incoming.length) return
  const bySeq = new Map(events.map((event) => [event.seq, event]))
  for (const event of incoming) bySeq.set(event.seq, event)
  events = [...bySeq.values()].sort((a, b) => a.seq - b.seq).slice(-800)
  cursor = Math.max(cursor, ...incoming.map((event) => event.seq))
  const latestControl = [...incoming].reverse().find((event) => event.type === "control.changed")
  if (latestControl?.data.control && ["agent", "shared", "human"].includes(String(latestControl.data.control))) control = String(latestControl.data.control) as ControlMode
  updateChrome()
  if (activeTab === "activity") renderActivity()
}

async function loadSnapshot(): Promise<void> {
  const payload = await api<{ workspace: JsonRecord; events: LiveEvent[] }>("/api/live/snapshot")
  control = String(payload.workspace.control || "agent") as ControlMode
  events = payload.events || []
  cursor = Number(payload.workspace.seq || events.at(-1)?.seq || 0)
  connected = true
  connectionMessage = "Live"
  updateChrome()
  renderCurrentTab()
}

async function pollEvents(generation: number): Promise<void> {
  while (config && generation === pollGeneration) {
    try {
      const payload = await api<{ events: LiveEvent[]; cursor: number; control: ControlMode }>(`/api/live/events?after=${cursor}&timeout=25`)
      if (generation !== pollGeneration) return
      if (payload.control) control = payload.control
      mergeEvents(payload.events || [])
      cursor = Math.max(cursor, Number(payload.cursor || 0))
      connected = true
      connectionMessage = "Live"
      updateChrome()
      if (payload.events?.some((event) => ["tool.completed", "tool.failed", "human.action"].includes(event.type)) && Date.now() - lastPassiveRefresh > 1500) void refreshAllCore()
    } catch (error) {
      if (generation !== pollGeneration) return
      connected = false
      connectionMessage = "Reconnecting"
      updateChrome()
      await new Promise((resolve) => setTimeout(resolve, 1200))
    }
  }
}

function configureFromToolResult(result: unknown): void {
  const value = result as { _meta?: JsonRecord; structuredContent?: JsonRecord }
  const hidden = value?._meta?.["local-shell-mcp/live"] as JsonRecord | undefined
  const structured = value?.structuredContent || {}
  const token = String(hidden?.token || "")
  const apiBase = String(hidden?.apiBase || structured.api_base || "")
  if (!token || !apiBase) {
    connectionMessage = "Live credentials unavailable"
    renderCurrentTab()
    return
  }
  config = {
    token,
    apiBase,
    uiPath: String(hidden?.uiPath || structured.ui_path || "/ui"),
    workspaceId: String(hidden?.workspaceId || structured.workspace_id || ""),
    machine: String(structured.machine || "local"),
    cwd: String(structured.cwd || "."),
  }
  terminalMachine = config.machine
  fileMachine = config.machine
  filePath = config.cwd
  pollGeneration += 1
  const generation = pollGeneration
  connectionMessage = "Connecting"
  renderCurrentTab()
  void (async () => {
    try {
      await loadSnapshot()
      await refreshAllCore()
      await refreshCurrent(false)
      void pollEvents(generation)
    } catch (error) {
      connected = false
      connectionMessage = "Connection failed"
      updateChrome()
      renderCurrentTab()
      notify(error instanceof Error ? error.message : String(error), "danger")
    }
  })()
}

function applyHostContext(context: unknown): void {
  const value = (context || {}) as JsonRecord
  const theme = value.theme
  if (theme === "light" || theme === "dark") applyDocumentTheme(theme)
  const styles = value.styles as JsonRecord | undefined
  if (styles?.variables && typeof styles.variables === "object") applyHostStyleVariables(styles.variables as never)
  const css = styles?.css as JsonRecord | undefined
  if (typeof css?.fonts === "string") applyHostFonts(css.fonts)
  const mode = String(value.displayMode || "inline")
  document.documentElement.dataset.displayMode = mode
}

app.ontoolresult = (result) => configureFromToolResult(result)
app.ontoolinput = (input) => {
  const args = input.arguments || {}
  if (typeof args.machine === "string") terminalMachine = fileMachine = args.machine
  if (typeof args.cwd === "string") filePath = args.cwd
}
app.onhostcontextchanged = (context) => applyHostContext(context)

shell()

void (async () => {
  try {
    await app.connect()
    applyHostContext(app.getHostContext())
  } catch (error) {
    connected = false
    connectionMessage = "Host bridge unavailable"
    updateChrome()
    renderCurrentTab()
    console.error("Unable to initialize MCP App bridge", error)
  }
})()

setInterval(() => {
  if (config && Date.now() - lastPassiveRefresh > 6_000) void refreshAllCore()
}, 6_000)

window.addEventListener("beforeunload", () => {
  pollGeneration += 1
  destroyTerminal()
  void app.close()
})
