import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
} from "@modelcontextprotocol/ext-apps"
import { FitAddon } from "@xterm/addon-fit"
import { Terminal } from "@xterm/xterm"
import {
  activityDestination,
  activityIntent,
  basename,
  escapeHtml,
  eventDetail,
  eventTitle,
  eventTone,
  formatBytes,
  formatClock,
  isOperationalActivityEvent,
  joinPath,
  toggleWorkspaceDisplayMode,
  parentPath,
  reconnectDelayMs,
  renderDiffHtml,
  toolResultFromOpenAiGlobals,
  truncateContext,
  type DisplayMode,
  type LiveEvent,
} from "./live-workspace-utils"

type JsonRecord = Record<string, unknown>

class LiveApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "LiveApiError"
    this.status = status
  }
}

function isLiveCredentialError(error: unknown): boolean {
  return error instanceof LiveApiError && (error.status === 401 || error.status === 403)
}

function waitForRetry(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds))
}

type Machine = { name: string; status?: string; workdir?: string; version?: string; platform?: string }
type TerminalSession = { session_id: string; backend?: string; created?: number; attached?: number; cwd?: string; name?: string }
type FileEntry = { name: string; path: string; type: string; size?: number; modified?: number; hidden?: boolean }

type LiveConfig = {
  token: string
  apiBase: string
  uiPath: string
  liveId: string
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
  { availableDisplayModes: ["pip", "fullscreen"] },
)

const root = document.createElement("div")
root.id = "live-workspace-root"
document.body.append(root)

let config: LiveConfig | null = null
let events: LiveEvent[] = []
let cursor = 0
let pollGeneration = 0
let connected = false
let connectionMessage = "Waiting for Live Workspace…"
let activeTab = "activity"
let displayMode: DisplayMode = "pip"
let bootstrap: JsonRecord | null = null
let dashboard: Dashboard | null = null
let machines: Machine[] = []
let lastPassiveRefresh = 0
let passiveRefreshing = false
let coreRefreshQueued = false
let activityExpandedCallId = ""
const activityAuditDetails = new Map<string, JsonRecord>()
let activityDiscoveryInitialized = false
let knownActiveJobs = new Set<string>()
let knownStandaloneSessions = new Set<string>()

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

let workloadMachine = "local"
let diffMachine = "local"
let diffCwd = "."
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
          <button class="icon-button" data-action="expand" title="Fullscreen">${icon("expand")}</button>
        </div>
      </header>
      <section class="status-strip">
        <div class="current-operation"><span class="pulse" data-role="op-pulse"></span><div><small>Current</small><strong data-role="current-op">No active tool call</strong><span data-role="current-detail">Waiting for activity</span></div></div>
        <div class="status-stat compact-stat"><small>Machines</small><strong data-role="machine-count">—</strong></div>
        <div class="status-stat compact-stat"><small>Workload</small><strong data-role="workload-count">—</strong></div>
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
  root.querySelectorAll<HTMLButtonElement>("[data-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === activeTab)
  })
  const expandButton = qs<HTMLButtonElement>("[data-action=expand]")
  if (expandButton) {
    const fullscreen = displayMode === "fullscreen"
    expandButton.classList.toggle("active", fullscreen)
    expandButton.title = fullscreen ? "Return to floating window" : "Fullscreen"
    expandButton.setAttribute("aria-label", expandButton.title)
  }

  const running = currentRunningEvent()
  const activeJob = dashboard?.jobs?.[0]
  const activeSession = dashboard?.sessions?.[0]
  const current = qs<HTMLElement>("[data-role=current-op]")
  const detail = qs<HTMLElement>("[data-role=current-detail]")
  const pulse = qs<HTMLElement>("[data-role=op-pulse]")
  if (current) {
    if (running) current.textContent = activityIntent(running)
    else if (activeJob) current.textContent = `Background: ${String(activeJob.name || activeJob.job_id || "job")}`
    else if (activeSession) current.textContent = `Terminal: ${String(activeSession.name || activeSession.session_id || "session")}`
    else current.textContent = "Idle"
  }
  if (detail) {
    if (running) detail.textContent = eventDetail(running) || "In progress"
    else if (activeJob) detail.textContent = String(activeJob.command || activeJob.status || "running")
    else if (activeSession) detail.textContent = String(activeSession.cwd || activeSession.backend || "ready")
    else detail.textContent = latestCompletedSummary()
  }
  pulse?.classList.toggle("active", Boolean(running || activeJob))

  const machineCount = qs<HTMLElement>("[data-role=machine-count]")
  const online = machines.filter((item) => item.status === "online" || item.name === "local").length
  if (machineCount) machineCount.textContent = `${machines.length || 1} · ${online || 1} online`
  const workload = (dashboard?.jobs?.length || 0) + (dashboard?.session_count || dashboard?.sessions?.length || 0)
  const workloadCount = qs<HTMLElement>("[data-role=workload-count]")
  if (workloadCount) workloadCount.textContent = workload ? `${workload} active` : "0"

}

function operationalEvents(): LiveEvent[] {
  return events.filter(isOperationalActivityEvent)
}

function currentRunningEvent(): LiveEvent | null {
  const visible = operationalEvents()
  const completed = new Set(visible.filter((event) => event.type === "tool.completed" || event.type === "tool.failed").map((event) => String(event.data.call_id || "")))
  for (let index = visible.length - 1; index >= 0; index -= 1) {
    const event = visible[index]
    if (event.type === "tool.started" && !completed.has(String(event.data.call_id || ""))) return event
  }
  return null
}

function latestCompletedSummary(): string {
  const visible = operationalEvents()
  for (let index = visible.length - 1; index >= 0; index -= 1) {
    const event = visible[index]
    if (["tool.completed", "tool.failed", "human.action"].includes(event.type)) return activityIntent(event)
  }
  return connected ? "Ready" : "Waiting for connection"
}

function onRootClick(event: MouseEvent): void {
  if ((event.target as HTMLElement).closest(".timeline-detail")) return
  const target = (event.target as HTMLElement).closest<HTMLElement>("[data-tab],[data-action]")
  if (!target) return
  if (target.dataset.tab) void switchTab(target.dataset.tab)
  if (target.dataset.action) void handleAction(target.dataset.action, target)
}

async function handleAction(action: string, target: HTMLElement): Promise<void> {
  try {
    if (action === "expand") await requestDisplayMode(toggleWorkspaceDisplayMode(displayMode))
    else if (action === "refresh") await refreshCurrent(true)
    else if (action === "activity-ask") await askAboutLatestActivity()
    else if (action === "activity-open-detail") await toggleActivityDetail(target.dataset.callId || "")
    else if (action === "activity-open-terminal") {
      terminalMachine = target.dataset.machine || "local"
      selectedSession = target.dataset.session || ""
      await switchTab("terminal")
    }
    else if (action === "activity-open-jobs") {
      workloadMachine = target.dataset.machine || "local"
      await switchTab("jobs")
    }
    else if (action === "activity-open-files") {
      const path = target.dataset.path || ""
      const tool = target.dataset.tool || ""
      fileMachine = target.dataset.machine || "local"
      if (path) {
        if (["list_files", "tree_view", "glob_search", "grep_search", "search"].includes(tool)) {
          filePath = path
          selectedFile = ""
        } else {
          filePath = parentPath(path)
          selectedFile = path
        }
      }
      await switchTab("files")
      if (selectedFile && fileEntries.some((entry) => entry.path === selectedFile)) await selectFile(selectedFile)
    }
    else if (action === "activity-open-diff") {
      diffMachine = target.dataset.machine || "local"
      diffCwd = target.dataset.cwd || config?.cwd || "."
      gitSnapshot = null
      await switchTab("diff")
    }
    else if (action === "activity-open-remotes") await switchTab("remotes")
    else if (action === "activity-open-audit") await switchTab("audit")
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

async function requestDisplayMode(mode: "fullscreen" | "pip"): Promise<void> {
  try {
    const result = await app.requestDisplayMode({ mode })
    if (result.mode === "pip" || result.mode === "fullscreen") displayMode = result.mode
    document.documentElement.dataset.displayMode = displayMode
    updateChrome()
  } catch (error) {
    notify(`Host did not change display mode: ${error instanceof Error ? error.message : String(error)}`, "warning")
  }
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
  const visible = operationalEvents()
  const recent = [...visible].reverse().slice(0, 120)
  const running = currentRunningEvent()
  const completed = visible.filter((event) => event.type === "tool.completed").length
  const failed = visible.filter((event) => event.type === "tool.failed").length
  const human = visible.filter((event) => event.actor === "human").length
  mainNode().innerHTML = `
    <section class="view activity-view">
      <div class="view-toolbar"><div><h2>Operational activity</h2><p>What ChatGPT is doing in LSM, with direct paths to the relevant workspace view.</p></div><div class="toolbar-actions"><button class="button" data-action="activity-ask">${icon("chat")}Ask about latest</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      ${activityFocusCards()}
      <div class="metric-row">
        <div><small>Current</small><strong>${running ? escapeHtml(activityIntent(running)) : dashboard?.jobs?.length ? "Background work" : dashboard?.sessions?.length ? "Terminal ready" : "Idle"}</strong><span>${running ? escapeHtml(eventDetail(running) || "running") : dashboard?.jobs?.length ? escapeHtml(String(dashboard.jobs[0]?.name || dashboard.jobs[0]?.job_id || "job")) : dashboard?.sessions?.length ? escapeHtml(String(dashboard.sessions[0]?.name || dashboard.sessions[0]?.session_id || "session")) : "Ready"}</span></div>
        <div><small>Completed</small><strong>${completed}</strong><span>operations</span></div>
        <div><small>Failures</small><strong>${failed}</strong><span>${failed ? "needs attention" : "none"}</span></div>
        <div><small>Human actions</small><strong>${human}</strong><span>interventions</span></div>
      </div>
      <div class="panel activity-panel">
        <div class="panel-head"><strong>Timeline</strong><span>${recent.length} recent events</span></div>
        <div class="timeline">${recent.length ? recent.map(activityRow).join("") : '<div class="empty-state">No execution activity yet. Start a task and this view will follow it.</div>'}</div>
      </div>
    </section>`
}

function activityFocusCards(): string {
  const jobs = dashboard?.jobs || []
  const sessions = dashboard?.sessions || []
  if (!jobs.length && !sessions.length) return ""
  const cards: string[] = []
  for (const job of jobs.slice(0, 2)) {
    const sessionId = String(job.session_id || "")
    const action = sessionId ? "activity-open-terminal" : "activity-open-jobs"
    cards.push(`<button class="focus-card job" data-action="${action}" data-session="${escapeHtml(sessionId)}" data-machine="${escapeHtml(String(job.machine || workloadMachine || "local"))}"><small>Background job</small><strong>${escapeHtml(String(job.name || job.job_id || "job"))}</strong><span>${escapeHtml(String(job.status || "running"))} · ${sessionId ? "View output" : "Open jobs"}</span></button>`)
  }
  for (const session of sessions.slice(0, Math.max(0, 3 - cards.length))) {
    cards.push(`<button class="focus-card terminal" data-action="activity-open-terminal" data-session="${escapeHtml(String(session.session_id || ""))}" data-machine="${escapeHtml(String(session.machine || workloadMachine || "local"))}"><small>Persistent terminal</small><strong>${escapeHtml(String(session.name || session.session_id || "terminal"))}</strong><span>Open terminal</span></button>`)
  }
  return `<div class="activity-focus">${cards.join("")}</div>`
}

function activityRow(event: LiveEvent): string {
  const detail = eventDetail(event)
  const destination = activityDestination(event)
  const callId = String(event.data.call_id || "")
  let action = ""
  let actionLabel = ""
  if (destination === "terminal") {
    action = `data-action="activity-open-terminal" data-session="${escapeHtml(String(event.data.session_id || ""))}" data-machine="${escapeHtml(String(event.data.machine || "local"))}"`
    actionLabel = "Open terminal"
  } else if (destination === "jobs") {
    action = `data-action="activity-open-jobs" data-machine="${escapeHtml(String(event.data.machine || "local"))}"`
    actionLabel = "Open jobs"
  } else if (destination === "files") {
    const rawPath = event.data.path ?? event.data.cwd
    const path = Array.isArray(rawPath) ? String(rawPath[0] || "") : String(rawPath || "")
    action = `data-action="activity-open-files" data-tool="${escapeHtml(String(event.data.tool || ""))}" data-path="${escapeHtml(path)}" data-machine="${escapeHtml(String(event.data.machine || "local"))}"`
    actionLabel = "Open files"
  } else if (destination === "diff") {
    action = `data-action="activity-open-diff" data-machine="${escapeHtml(String(event.data.machine || "local"))}" data-cwd="${escapeHtml(String(event.data.cwd || config?.cwd || "."))}"`
    actionLabel = "View diff"
  } else if (destination === "remotes") {
    action = `data-action="activity-open-remotes"`
    actionLabel = "Open remotes"
  } else if (destination === "audit") {
    action = `data-action="activity-open-audit"`
    actionLabel = "Open audit"
  } else if (destination === "detail" && callId) {
    action = `data-action="activity-open-detail" data-call-id="${escapeHtml(callId)}"`
    actionLabel = activityExpandedCallId === callId ? "Hide output" : "View output"
  }
  const expanded = callId && activityExpandedCallId === callId ? activityDetailHtml(callId) : ""
  return `<div class="timeline-row ${eventTone(event)} ${action ? "clickable" : ""}" ${action}><div class="timeline-marker"><span></span></div><div class="timeline-copy"><div><strong>${escapeHtml(eventTitle(event))}</strong><span class="actor ${escapeHtml(event.actor)}">${escapeHtml(event.actor)}</span>${actionLabel ? `<span class="timeline-action">${escapeHtml(actionLabel)}</span>` : ""}</div>${detail ? `<p>${escapeHtml(detail)}</p>` : ""}</div><time>${escapeHtml(formatClock(event.ts))}</time>${expanded}</div>`
}

function activityDetailHtml(callId: string): string {
  const detail = activityAuditDetails.get(callId)
  if (!detail) return '<div class="timeline-detail loading-detail">Loading output…</div>'
  const output = detail.output as JsonRecord | undefined
  const structured = (output?.structuredContent || output?.structured_content) as JsonRecord | undefined
  const payload = (structured?.data || output?.data || structured || output || detail) as unknown
  if (payload && typeof payload === "object" && !Array.isArray(payload)) {
    const record = payload as JsonRecord
    const chunks: string[] = []
    if (record.command) chunks.push(`$ ${String(record.command)}`)
    if (record.stdout) chunks.push(String(record.stdout))
    if (record.stderr) chunks.push(`stderr:\n${String(record.stderr)}`)
    if (chunks.length) return `<pre class="timeline-detail">${escapeHtml(truncateContext(chunks.join("\n"), 24_000))}</pre>`
  }
  return `<pre class="timeline-detail">${escapeHtml(truncateContext(JSON.stringify(payload, null, 2), 24_000))}</pre>`
}

async function toggleActivityDetail(callId: string): Promise<void> {
  if (!callId) return
  if (activityExpandedCallId === callId) {
    activityExpandedCallId = ""
    renderActivity()
    return
  }
  activityExpandedCallId = callId
  renderActivity()
  if (activityAuditDetails.has(callId)) return
  try {
    const detail = await api<JsonRecord>(`/api/ui/audit/detail?id=${encodeURIComponent(`call:${callId}`)}`)
    activityAuditDetails.set(callId, detail)
    if (activityExpandedCallId === callId && activeTab === "activity") renderActivity()
  } catch (error) {
    if (activityExpandedCallId === callId) activityExpandedCallId = ""
    if (activeTab === "activity") renderActivity()
    notify(error instanceof Error ? error.message : String(error), "warning")
  }
}

async function askAboutLatestActivity(): Promise<void> {
  const recent = operationalEvents().slice(-20)
  await app.updateModelContext({
    content: [{ type: "text", text: `Live Workspace recent operational activity:\n${recent.map((event) => `${formatClock(event.ts)} ${eventTitle(event)} — ${eventDetail(event)}`).join("\n")}` }],
    structuredContent: { liveWorkspaceEvents: recent },
  })
  await app.sendMessage({ role: "user", content: [{ type: "text", text: "Review the recent Live Workspace activity and tell me what matters, especially any failure, blocker, or next action." }] })
}

function renderTerminal(): void {
  const session = terminalSessions.find((item) => item.session_id === selectedSession)
  mainNode().innerHTML = `
    <section class="view terminal-view">
      <div class="view-toolbar terminal-toolbar"><div class="toolbar-left"><label>Machine<select data-role="terminal-machine">${machineOptions(terminalMachine)}</select></label><label>Session<select data-role="terminal-session"><option value="">${terminalSessions.length ? "Select session" : "No sessions"}</option>${terminalSessions.map((item) => `<option value="${escapeHtml(item.session_id)}"${item.session_id === selectedSession ? " selected" : ""}>${escapeHtml(item.name || item.session_id)}</option>`).join("")}</select></label></div><div class="toolbar-actions"><button class="button" data-action="terminal-new">New</button><button class="button" data-action="terminal-kill" ${selectedSession ? "" : "disabled"}>Kill</button><button class="button" data-action="terminal-copy">${icon("copy")}Copy</button><button class="button" data-action="terminal-ctrl-c" ${selectedSession ? "" : "disabled"}>Ctrl-C</button><button class="button" data-action="terminal-reconnect">Reconnect</button></div></div>
      <div class="terminal-card">
        <div class="terminal-title"><div><span class="terminal-led ${selectedSession ? "online" : ""}"></span><strong>${escapeHtml(session?.name || selectedSession || "Persistent terminal")}</strong><small>${escapeHtml(terminalMachine)}${session?.backend ? ` · ${escapeHtml(session.backend)}` : ""}</small></div><span>Collaborative input</span></div>
        <div class="terminal-host" data-role="terminal-host"></div>
        <form class="command-dock" data-role="command-form"><span>$</span><input data-role="command-input" autocomplete="off" placeholder="Send command to attached session" ${selectedSession ? "" : "disabled"}/><button ${selectedSession ? "" : "disabled"}>Send</button></form>
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
    cursorBlink: true,
    cursorStyle: "bar",
    disableStdin: false,
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
  if (!selectedSession) return
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
  const name = await promptValue("New terminal", "Optional name", "", `Create a persistent shell on ${terminalMachine}.`)
  if (name === null) return
  const requestMachine = terminalMachine
  const requestCwd = config?.cwd || "."
  const result = await api<JsonRecord>("/api/ui/terminals/start", { method: "POST", body: JSON.stringify({ machine: requestMachine, cwd: requestCwd, name: name || null }) })
  if (terminalMachine !== requestMachine) return
  selectedSession = String(result.session_id || "")
  await refreshTerminals()
}

async function killTerminal(): Promise<void> {
  if (!selectedSession) return
  const requestMachine = terminalMachine
  const requestSession = selectedSession
  await api("/api/ui/terminals/kill", { method: "POST", body: JSON.stringify({ machine: requestMachine, session_id: requestSession }) })
  if (terminalMachine !== requestMachine || selectedSession !== requestSession) return
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
  const selected = fileEntries.find((entry) => entry.path === selectedFile)
  mainNode().innerHTML = `
    <section class="view files-view">
      <div class="view-toolbar files-toolbar"><div class="path-controls"><label>Machine<select data-role="file-machine">${machineOptions(fileMachine)}</select></label><button class="button" data-action="file-up">Up</button><input data-role="file-path" value="${escapeHtml(filePath)}" aria-label="Path"/></div><div class="toolbar-actions"><button class="button" data-action="file-new">New file</button><button class="button" data-action="file-new-dir">New folder</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="files-grid">
        <section class="panel file-list-panel"><div class="panel-head"><strong>${escapeHtml(fileMachine)}:${escapeHtml(filePath)}</strong><span>${fileEntries.length} entries</span></div><div class="file-list">${fileEntries.length ? fileEntries.map(fileRow).join("") : '<div class="empty-state">Directory is empty.</div>'}</div></section>
        <section class="panel preview-panel"><div class="panel-head"><div><strong>${escapeHtml(selected?.name || "Preview")}</strong><span>${selected ? `${escapeHtml(selected.type)} · ${formatBytes(selected.size)}` : "Choose a file"}</span></div><div class="preview-actions">${selected?.type === "file" ? `<button class="text-button" data-action="file-context">Send context</button><button class="text-button" data-action="file-ask">Ask ChatGPT</button><button class="text-button" data-action="file-edit">Edit</button><button class="text-button danger" data-action="file-delete">Delete</button>` : ""}</div></div><div class="file-preview" data-role="file-preview">${renderFilePreview()}</div></section>
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
  const name = await promptValue(directory ? "New folder" : "New file", "Name", "", `Create inside ${filePath}.`)
  if (!name?.trim()) return
  const requestMachine = fileMachine
  const requestParent = filePath
  const path = joinPath(requestParent, name.trim())
  await api(`/api/ui/files/${directory ? "mkdir" : "touch"}`, { method: "POST", body: JSON.stringify({ machine: requestMachine, path }) })
  if (fileMachine !== requestMachine || filePath !== requestParent) return
  selectedFile = path
  await refreshFiles()
}

async function deleteSelectedFile(): Promise<void> {
  if (!selectedFile) return
  const requestMachine = fileMachine
  const requestPath = selectedFile
  const entry = fileEntries.find((item) => item.path === requestPath)
  const confirmation = await promptValue("Delete entry", `Type ${basename(requestPath)} to confirm`, "", "This action cannot be undone by the Live Workspace.")
  if (confirmation !== basename(requestPath)) return
  await api("/api/ui/files/delete", { method: "POST", body: JSON.stringify({ machine: requestMachine, path: requestPath, recursive: entry?.type === "dir" }) })
  if (fileMachine !== requestMachine || selectedFile !== requestPath) return
  selectedFile = ""
  await refreshFiles()
}

async function beginFileEdit(): Promise<void> {
  if (!selectedFile) return
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
  if (!selectedFile) return
  const editor = qs<HTMLTextAreaElement>("[data-role=file-editor]")
  if (!editor) return
  const requestMachine = fileMachine
  const requestPath = selectedFile
  const requestSha = fileEditSha
  await api("/api/ui/files/write", { method: "POST", body: JSON.stringify({ machine: requestMachine, path: requestPath, content: editor.value, overwrite: true, expected_sha256: requestSha || null }) })
  if (fileMachine !== requestMachine || selectedFile !== requestPath) return
  fileEditing = false
  filePreview = null
  await selectFile(requestPath)
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
    <section class="view diff-view"><div class="view-toolbar"><div><h2>Working tree diff</h2><p>${escapeHtml(gitSnapshot?.machine || diffMachine)}:${escapeHtml(gitSnapshot?.cwd || diffCwd)} · unstaged and staged changes</p></div><div class="toolbar-actions"><button class="button" data-action="diff-context">Send context</button><button class="button" data-action="diff-ask">${icon("chat")}Ask for review</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="diff-layout"><section class="panel status-panel"><div class="panel-head"><strong>Git status</strong><span>${escapeHtml(gitSnapshot?.cwd || diffCwd)}</span></div><pre>${escapeHtml(status || "Clean")}</pre></section><section class="panel diff-panel"><div class="panel-head"><strong>Changes</strong><span>${diff ? `${diff.split("\n").length} lines` : "clean"}</span></div><div class="diff-code">${gitSnapshot ? renderDiffHtml(diff) : '<div class="loading small"><span></span>Loading diff…</div>'}</div></section></div>
    </section>`
}

async function refreshDiff(): Promise<void> {
  if (!config) return
  const requestLiveId = config.liveId
  const requestMachine = diffMachine
  const requestCwd = diffCwd
  const snapshot = await api<{ machine?: string; cwd: string; status: JsonRecord; diff: JsonRecord }>(`/api/live/git?machine=${encodeURIComponent(requestMachine)}&cwd=${encodeURIComponent(requestCwd)}`)
  if (!config || config.liveId !== requestLiveId || diffMachine !== requestMachine || diffCwd !== requestCwd) return
  gitSnapshot = snapshot
  if (activeTab === "diff") renderDiff()
}

async function shareDiff(ask: boolean): Promise<void> {
  if (!gitSnapshot) await refreshDiff()
  const status = String(gitSnapshot?.status.stdout || "")
  const diff = truncateContext(String(gitSnapshot?.diff.stdout || ""), 28_000)
  await app.updateModelContext({ content: [{ type: "text", text: `Live Workspace git status (${gitSnapshot?.machine || diffMachine}):\n${status}\n\nDiff:\n${diff}` }], structuredContent: { git: { machine: gitSnapshot?.machine || diffMachine, cwd: gitSnapshot?.cwd || diffCwd, status } } })
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
  const sessionId = String(job.session_id || "")
  const body = `<span class="state-dot ${escapeHtml(status)}"></span><div><strong>${escapeHtml(String(job.name || job.job_id || "job"))}</strong><p>${escapeHtml(String(job.command || job.kind || ""))}</p></div><div class="object-meta"><span>${escapeHtml(status)}</span><small>${sessionId ? "view output" : escapeHtml(String(job.machine || "local"))}</small></div>`
  return sessionId
    ? `<button class="object-row clickable" data-open-session="${escapeHtml(sessionId)}" data-machine="${escapeHtml(String(job.machine || "local"))}">${body}</button>`
    : `<div class="object-row">${body}</div>`
}

function sessionRow(session: JsonRecord): string {
  return `<button class="object-row clickable" data-open-session="${escapeHtml(String(session.session_id || ""))}"><span class="state-dot running"></span><div><strong>${escapeHtml(String(session.name || session.session_id || "terminal"))}</strong><p>${escapeHtml(String(session.backend || "persistent shell"))}</p></div><div class="object-meta"><span>${escapeHtml(String(session.machine || "local"))}</span><small>terminal</small></div></button>`
}

function wireJobRows(): void {
  root.querySelectorAll<HTMLButtonElement>("[data-open-session]").forEach((row) => {
    row.addEventListener("click", () => {
      selectedSession = row.dataset.openSession || ""
      const source = [...(dashboard?.jobs || []), ...(dashboard?.sessions || [])].find((item) => item.session_id === selectedSession)
      terminalMachine = row.dataset.machine || String(source?.machine || workloadMachine || "local")
      void switchTab("terminal")
    })
  })
}

function trackActivityDiscoveries(next: Dashboard): void {
  const jobs = next.jobs || []
  const sessions = next.sessions || []
  const nextJobs = new Set(jobs.map((job) => `${String(job.machine || "local")}:${String(job.job_id || job.session_id || job.name || "job")}`))
  const nextSessions = new Set(sessions.map((session) => `${String(session.machine || "local")}:${String(session.session_id || session.name || "terminal")}`))
  if (!activityDiscoveryInitialized) {
    knownActiveJobs = nextJobs
    knownStandaloneSessions = nextSessions
    activityDiscoveryInitialized = true
    return
  }
  for (const job of jobs) {
    const key = `${String(job.machine || "local")}:${String(job.job_id || job.session_id || job.name || "job")}`
    if (!knownActiveJobs.has(key)) notify(`Background job started: ${String(job.name || job.job_id || "job")}`, "info")
  }
  for (const session of sessions) {
    const key = `${String(session.machine || "local")}:${String(session.session_id || session.name || "terminal")}`
    if (!knownStandaloneSessions.has(key)) notify(`Terminal ready: ${String(session.name || session.session_id || "terminal")}`, "info")
  }
  knownActiveJobs = nextJobs
  knownStandaloneSessions = nextSessions
}

function renderRemotes(): void {
  const enabled = bootstrap ? Boolean((bootstrap.features as JsonRecord | undefined)?.remote) : true
  const rows = (remoteSnapshot?.machines as Machine[] | undefined) || []
  mainNode().innerHTML = `
    <section class="view remotes-view"><div class="view-toolbar"><div><h2>Remote machines</h2><p>Worker connectivity, workdirs and administrative actions.</p></div><div class="toolbar-actions"><button class="button primary" data-action="remote-invite" ${enabled ? "" : "disabled"}>Invite machine</button><button class="button" data-action="refresh">${icon("refresh")}Refresh</button></div></div>
      <div class="panel remote-panel"><div class="panel-head"><strong>Machines</strong><span>${enabled ? `${rows.length} registered` : "remote support disabled"}</span></div><div class="remote-grid">${rows.length ? rows.map(remoteCard).join("") : `<div class="empty-state">${enabled ? "No remote workers registered." : "Remote worker support is disabled."}</div>`}</div></div>
    </section>`
}

function remoteCard(machine: Machine): string {
  return `<article class="remote-card"><div class="remote-head"><span class="machine-icon">${icon("remotes")}</span><div><strong>${escapeHtml(machine.name)}</strong><span class="status-chip ${machine.status === "online" ? "online" : "offline"}">${escapeHtml(machine.status || "unknown")}</span></div></div><dl><div><dt>Workdir</dt><dd>${escapeHtml(machine.workdir || "—")}</dd></div><div><dt>Version</dt><dd>${escapeHtml(machine.version || "—")}</dd></div><div><dt>Platform</dt><dd>${escapeHtml(machine.platform || "—")}</dd></div></dl><footer><button class="text-button" data-action="remote-rename" data-machine="${escapeHtml(machine.name)}">Rename</button><button class="text-button danger" data-action="remote-revoke" data-machine="${escapeHtml(machine.name)}">Revoke</button></footer></article>`
}

async function refreshRemotes(): Promise<void> {
  if (bootstrap && !(bootstrap.features as JsonRecord | undefined)?.remote) { remoteSnapshot = { machines: [] }; if (activeTab === "remotes") renderRemotes(); return }
  remoteSnapshot = await api<JsonRecord>("/api/ui/remotes")
  if (activeTab === "remotes") renderRemotes()
}

async function createRemoteInvite(): Promise<void> {
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

function resetFileTarget(machine: string, path: string): void {
  fileMachine = machine
  filePath = path
  fileEntries = []
  selectedFile = ""
  filePreview = null
  fileEditing = false
  fileEditContent = ""
  fileEditSha = ""
}

function resetTerminalTarget(machine: string): void {
  terminalMachine = machine
  terminalSessions = []
  selectedSession = ""
  terminalSocket?.close()
  terminalSocket = null
}

function resetWorkspaceTarget(machine: string, cwd: string): void {
  workloadMachine = machine
  diffMachine = machine
  diffCwd = cwd
  gitSnapshot = null
  dashboard = null
  activityDiscoveryInitialized = false
  knownActiveJobs.clear()
  knownStandaloneSessions.clear()
  activityExpandedCallId = ""
  activityAuditDetails.clear()
  resetFileTarget(machine, cwd)
  resetTerminalTarget(machine)
}

function replaceMachineSelection(machine: string, replacement: string, replacementCwd?: string): void {
  if (config?.machine === machine) {
    config = { ...config, machine: replacement, cwd: replacementCwd ?? config.cwd }
    gitSnapshot = null
    dashboard = null
  }
  if (fileMachine === machine) {
    resetFileTarget(replacement, replacementCwd ?? filePath)
  }
  if (terminalMachine === machine) {
    resetTerminalTarget(replacement)
  }
  if (workloadMachine === machine) workloadMachine = replacement
  if (diffMachine === machine) {
    diffMachine = replacement
    if (replacementCwd) diffCwd = replacementCwd
    gitSnapshot = null
  }
}

async function renameRemote(machine: string): Promise<void> {
  if (!machine) return
  const name = await promptValue("Rename remote", "New name", machine)
  if (!name?.trim() || name === machine) return
  const newName = name.trim()
  await api("/api/ui/remotes/rename", { method: "POST", body: JSON.stringify({ machine, new_name: newName }) })
  replaceMachineSelection(machine, newName)
  await refreshAllCore()
  await refreshRemotes()
}

async function revokeRemote(machine: string): Promise<void> {
  if (!machine) return
  const confirmation = await promptValue("Revoke remote", `Type ${machine} to confirm`, "", "The worker will need a new invitation to reconnect.")
  if (confirmation !== machine) return
  await api("/api/ui/remotes/revoke", { method: "POST", body: JSON.stringify({ machine }) })
  replaceMachineSelection(machine, "local", ".")
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
  if (!config) return
  const requestLiveId = config.liveId
  const requestMachine = workloadMachine
  const result = await api<Dashboard>(`/api/ui/dashboard?machine=${encodeURIComponent(requestMachine)}`)
  if (!config || config.liveId !== requestLiveId || workloadMachine !== requestMachine) return
  trackActivityDiscoveries(result)
  dashboard = result
  updateChrome()
  if (activeTab === "jobs") { renderJobs(); wireJobRows() }
}

async function refreshAllCore(): Promise<void> {
  if (!config) return
  if (passiveRefreshing) {
    coreRefreshQueued = true
    return
  }
  passiveRefreshing = true
  const requestLiveId = config.liveId
  const requestApiBase = config.apiBase
  let selectionChanged = false
  try {
    const boot = await api<JsonRecord>("/api/ui/bootstrap")
    if (!config || config.liveId !== requestLiveId || config.apiBase !== requestApiBase) {
      coreRefreshQueued = true
      return
    }
    bootstrap = boot
    const nested = boot.machines as JsonRecord | undefined
    machines = (nested?.machines as Machine[] | undefined) || []
    const available = new Set(machines.map((item) => item.name))
    const fallback = available.has("local") ? "local" : machines[0]?.name || "local"
    if (!available.has(config.machine)) {
      const missing = config.machine
      replaceMachineSelection(missing, fallback, ".")
      selectionChanged = true
    }
    const preferred = available.has(config.machine) ? config.machine : fallback
    if (!available.has(fileMachine)) {
      resetFileTarget(preferred, config.machine === preferred ? config.cwd : ".")
      selectionChanged = true
    }
    if (!available.has(terminalMachine)) {
      resetTerminalTarget(preferred)
      selectionChanged = true
    }
    if (!available.has(workloadMachine)) {
      workloadMachine = preferred
      dashboard = null
      selectionChanged = true
    }
    if (!available.has(diffMachine)) {
      diffMachine = preferred
      diffCwd = config.machine === preferred ? config.cwd : "."
      gitSnapshot = null
      selectionChanged = true
    }
    if (selectionChanged) renderCurrentTab()
    const dashboardMachine = workloadMachine
    const dash = await api<Dashboard>(`/api/ui/dashboard?machine=${encodeURIComponent(dashboardMachine || "local")}`)
    if (!config || config.liveId !== requestLiveId || config.apiBase !== requestApiBase || workloadMachine !== dashboardMachine) {
      coreRefreshQueued = true
      return
    }
    trackActivityDiscoveries(dash)
    dashboard = dash
    lastPassiveRefresh = Date.now()
    updateChrome()
    if (activeTab === "activity") renderActivity()
  } finally {
    passiveRefreshing = false
    if (coreRefreshQueued) {
      coreRefreshQueued = false
      queueMicrotask(() => void refreshAllCore())
    }
  }
  if (selectionChanged) {
    if (activeTab === "files") await refreshFiles()
    else if (activeTab === "terminal") await refreshTerminals()
    else if (activeTab === "diff") await refreshDiff()
    else if (activeTab === "jobs") { renderJobs(); wireJobRows() }
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
  try { payload = await response.json() as JsonRecord } catch { throw new LiveApiError(`Live API returned HTTP ${response.status}`, response.status) }
  if (!response.ok || payload.ok === false) throw new LiveApiError(String(payload.message || payload.detail || `HTTP ${response.status}`), response.status)
  return (payload.data ?? payload) as T
}

function mergeEvents(incoming: LiveEvent[]): void {
  if (!incoming.length) return
  const bySeq = new Map(events.map((event) => [event.seq, event]))
  for (const event of incoming) {
    bySeq.set(event.seq, event)
    if (event.type === "tool.completed" || event.type === "tool.failed") {
      const callId = String(event.data.call_id || "")
      if (callId) activityAuditDetails.delete(callId)
    }
  }
  events = [...bySeq.values()].sort((a, b) => a.seq - b.seq).slice(-800)
  cursor = Math.max(cursor, ...incoming.map((event) => event.seq))
  updateChrome()
  if (activeTab === "activity") renderActivity()
}

async function loadSnapshot(generation: number): Promise<boolean> {
  const payload = await api<{ channel: JsonRecord; events: LiveEvent[] }>("/api/live/snapshot")
  if (generation !== pollGeneration) return false
  events = payload.events || []
  cursor = Number(payload.channel.seq || events.at(-1)?.seq || 0)
  connected = true
  connectionMessage = "Live"
  updateChrome()
  renderCurrentTab()
  return true
}

async function pollEvents(generation: number): Promise<void> {
  while (config && generation === pollGeneration) {
    const payload = await api<{ events: LiveEvent[]; cursor: number }>(`/api/live/events?after=${cursor}&timeout=25`)
    if (generation !== pollGeneration) return
    mergeEvents(payload.events || [])
    cursor = Math.max(cursor, Number(payload.cursor || 0))
    connected = true
    connectionMessage = "Live"
    updateChrome()
    if (payload.events?.some((event) => ["tool.completed", "tool.failed", "human.action"].includes(event.type)) && Date.now() - lastPassiveRefresh > 1500) void refreshAllCore()
  }
}

async function runConnectionLoop(generation: number): Promise<void> {
  let attempt = 0
  let announcedRetry = false
  while (config && generation === pollGeneration) {
    try {
      connectionMessage = attempt ? "Reconnecting" : "Connecting"
      updateChrome()
      renderCurrentTab()
      if (!await loadSnapshot(generation)) return
      await refreshAllCore()
      if (generation !== pollGeneration) return
      await refreshCurrent(false)
      if (generation !== pollGeneration) return
      attempt = 0
      announcedRetry = false
      await pollEvents(generation)
      return
    } catch (caught) {
      if (!config || generation !== pollGeneration) return
      let error = caught
      if (isLiveCredentialError(error)) {
        const stale = config
        try {
          await refreshLiveCredentials({ machine: stale.machine, cwd: stale.cwd, live_id: stale.liveId }, true)
          return
        } catch (credentialError) {
          error = credentialError
        }
      }
      connected = false
      connectionMessage = "Reconnecting"
      updateChrome()
      renderCurrentTab()
      if (!announcedRetry) {
        announcedRetry = true
        notify(`Connection lost; retrying automatically (${error instanceof Error ? error.message : String(error)})`, "warning")
      }
      const delay = reconnectDelayMs(attempt)
      attempt += 1
      await waitForRetry(delay)
    }
  }
}

function activateLiveConfig(nextConfig: LiveConfig): void {
  if (
    config
    && config.token === nextConfig.token
    && config.apiBase === nextConfig.apiBase
    && config.liveId === nextConfig.liveId
    && config.machine === nextConfig.machine
    && config.cwd === nextConfig.cwd
  ) return
  const targetChanged = !config || config.machine !== nextConfig.machine || config.cwd !== nextConfig.cwd
  if (targetChanged) resetWorkspaceTarget(nextConfig.machine, nextConfig.cwd)
  config = nextConfig
  pollGeneration += 1
  const generation = pollGeneration
  connectionMessage = "Connecting"
  renderCurrentTab()
  void runConnectionLoop(generation)
}

let credentialRefresh: Promise<void> | null = null

async function requestLiveConfig(structured: JsonRecord, allowCreate: boolean): Promise<LiveConfig> {
  const machine = String(structured.machine || "local")
  const cwd = String(structured.cwd || ".")
  const liveId = String(structured.live_id || "")
  const invoke = (id: string) => app.callServerTool({
    name: "open_live_workspace",
    arguments: id ? { machine, cwd, live_id: id } : { machine, cwd },
  })
  let response
  try {
    response = await invoke(liveId)
  } catch (error) {
    if (!allowCreate || !liveId) throw error
    response = await invoke("")
  }
  if (response.isError && allowCreate && liveId) response = await invoke("")
  if (response.isError) {
    const message = response.content.find((item) => item.type === "text")
    throw new Error(message?.type === "text" ? message.text : "Live Workspace authorization failed")
  }
  const responseStructured = (response.structuredContent || {}) as JsonRecord
  const hidden = response._meta?.["local-shell-mcp/live"] as JsonRecord | undefined
  const token = String(hidden?.token || "")
  const apiBase = String(hidden?.apiBase || responseStructured.api_base || structured.api_base || "")
  if (!token || !apiBase) {
    throw new Error("ChatGPT omitted Live Workspace credentials from the app-initiated tool result")
  }
  return {
    token,
    apiBase,
    uiPath: String(hidden?.uiPath || responseStructured.ui_path || structured.ui_path || "/ui"),
    liveId: String(hidden?.liveId || responseStructured.live_id || structured.live_id || ""),
    machine: String(responseStructured.machine || machine),
    cwd: String(responseStructured.cwd || cwd),
  }
}

function refreshLiveCredentials(structured: JsonRecord, allowCreate = false): Promise<void> {
  if (credentialRefresh) return credentialRefresh
  credentialRefresh = (async () => {
    connectionMessage = "Authorizing Live Workspace…"
    renderCurrentTab()
    activateLiveConfig(await requestLiveConfig(structured, allowCreate))
  })().finally(() => {
    credentialRefresh = null
  })
  return credentialRefresh
}

async function recoverCredentialsForever(structured: JsonRecord): Promise<void> {
  let attempt = 0
  while (!config) {
    try {
      await refreshLiveCredentials(structured, true)
      return
    } catch (error) {
      connected = false
      connectionMessage = "Reconnecting"
      updateChrome()
      renderCurrentTab()
      if (attempt === 0) notify(`Live authorization unavailable; retrying automatically (${error instanceof Error ? error.message : String(error)})`, "warning")
      const delay = reconnectDelayMs(attempt)
      attempt += 1
      await waitForRetry(delay)
    }
  }
}

async function configureFromToolResult(result: unknown): Promise<void> {
  const value = result as { _meta?: JsonRecord; structuredContent?: JsonRecord }
  const hidden = value?._meta?.["local-shell-mcp/live"] as JsonRecord | undefined
  const structured = value?.structuredContent || {}
  const token = String(hidden?.token || "")
  const apiBase = String(hidden?.apiBase || structured.api_base || "")
  if (!token || !apiBase) {
    const announcedLiveId = String(structured.live_id || "")
    if (config && (!announcedLiveId || announcedLiveId === config.liveId)) return
    await recoverCredentialsForever(structured)
    return
  }
  activateLiveConfig({
    token,
    apiBase,
    uiPath: String(hidden?.uiPath || structured.ui_path || "/ui"),
    liveId: String(hidden?.liveId || structured.live_id || ""),
    machine: String(structured.machine || "local"),
    cwd: String(structured.cwd || "."),
  })
}

async function enterPreferredDisplayMode(): Promise<void> {
  const context = app.getHostContext()
  const available = context?.availableDisplayModes || []
  if (available.includes("pip")) {
    if (context?.displayMode !== "pip") await requestDisplayMode("pip")
    return
  }
  if (available.includes("fullscreen")) {
    if (context?.displayMode !== "fullscreen") await requestDisplayMode("fullscreen")
    return
  }
  notify("Host does not support floating or fullscreen Live Workspace", "warning")
}

function applyHostContext(context: unknown): void {
  const value = (context || {}) as JsonRecord
  const theme = value.theme
  if (theme === "light" || theme === "dark") applyDocumentTheme(theme)
  const styles = value.styles as JsonRecord | undefined
  if (styles?.variables && typeof styles.variables === "object") applyHostStyleVariables(styles.variables as never)
  const css = styles?.css as JsonRecord | undefined
  if (typeof css?.fonts === "string") applyHostFonts(css.fonts)
  const mode = String(value.displayMode || "")
  if (mode === "fullscreen" || mode === "pip") displayMode = mode
  document.documentElement.dataset.displayMode = displayMode
  updateChrome()
}

type OpenAiGlobalsWindow = Window & {
  openai?: unknown
}

function configureFromOpenAiGlobals(globals?: unknown): boolean {
  const result = toolResultFromOpenAiGlobals(globals ?? (window as OpenAiGlobalsWindow).openai)
  if (!result) return false
  void configureFromToolResult(result)
  return true
}

function onOpenAiGlobalsChanged(event: Event): void {
  const detail = (event as CustomEvent<{ globals?: unknown }>).detail
  configureFromOpenAiGlobals(detail?.globals)
}

let bridgeReady = false
let pendingToolResult: unknown = null
let initialToolResultResolve: ((result: unknown | null) => void) | null = null

function waitForInitialToolResult(timeoutMs: number): Promise<unknown | null> {
  if (pendingToolResult) {
    const result = pendingToolResult
    pendingToolResult = null
    return Promise.resolve(result)
  }
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      if (initialToolResultResolve === finish) initialToolResultResolve = null
      resolve(null)
    }, timeoutMs)
    const finish = (result: unknown | null) => {
      window.clearTimeout(timer)
      if (initialToolResultResolve === finish) initialToolResultResolve = null
      resolve(result)
    }
    initialToolResultResolve = finish
  })
}

app.ontoolresult = (result) => {
  if (initialToolResultResolve) {
    const resolve = initialToolResultResolve
    initialToolResultResolve = null
    resolve(result)
    return
  }
  if (!bridgeReady) {
    pendingToolResult = result
    return
  }
  void configureFromToolResult(result)
}
app.onhostcontextchanged = (context) => applyHostContext(context)
window.addEventListener("openai:set_globals", onOpenAiGlobalsChanged)

shell()

void (async () => {
  try {
    await app.connect()
    bridgeReady = true
    applyHostContext(app.getHostContext())
    await enterPreferredDisplayMode()
    const initialResult = await waitForInitialToolResult(300)
    if (initialResult) await configureFromToolResult(initialResult)
    else if (!configureFromOpenAiGlobals()) await recoverCredentialsForever({})
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
  window.removeEventListener("openai:set_globals", onOpenAiGlobalsChanged)
  void app.close()
})
