import type { LogicalSession, LogicalSessionsPayload } from "../types"
import {
  BaseController,
  escapeHtml,
  formatAge,
  formatDate,
  highlightedHtml,
  queryString,
  type NativePageContext,
} from "./common"

const SESSION_STATUSES = ["all", "active", "completed", "cancelled"] as const

type SessionFilter = (typeof SESSION_STATUSES)[number]

function sessionTone(status: string): string {
  if (status === "completed") return "success"
  if (status === "active") return "warning"
  return "neutral"
}

function textBlock(title: string, value: string | null | undefined): string {
  return `<section class="session-detail-block"><h4>${escapeHtml(title)}</h4><p>${value ? escapeHtml(value) : '<span class="session-muted">Not recorded</span>'}</p></section>`
}

function stringList(title: string, values: string[]): string {
  return `<section class="session-detail-block"><h4>${escapeHtml(title)}</h4>${values.length ? `<ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul>` : '<p><span class="session-muted">None</span></p>'}</section>`
}

export class SessionsController extends BaseController {
  private sessions: LogicalSession[] = []
  private counts: LogicalSessionsPayload["counts"] = { active: 0, completed: 0, cancelled: 0, total: 0 }
  private selectedId: string | null = null
  private detail: LogicalSession | null = null
  private filter: SessionFilter = "all"
  private loading = false
  private detailRequest = 0

  mount(root: HTMLElement): void {
    this.root = root
    this.root.innerHTML = `<section class="native-page sessions-page">
      <div class="sessions-summary" data-role="sessions-summary"></div>
      <div class="native-toolbar sessions-toolbar">
        <div><strong>Logical Sessions</strong><span class="toolbar-detail">Durable agent tasks scoped to the authenticated principal</span></div>
        <label class="sessions-filter"><span>Status</span><select data-filter="status">${SESSION_STATUSES.map((status) => `<option value="${status}">${status === "all" ? "All sessions" : status}</option>`).join("")}</select></label>
      </div>
      <div class="sessions-layout">
        <section class="native-panel sessions-list-panel">
          <header><div><h3>Sessions</h3><p data-role="sessions-count">Loading…</p></div></header>
          <div class="sessions-list" data-role="sessions-list"><div class="native-loading">Loading logical sessions…</div></div>
        </section>
        <section class="native-panel sessions-detail-panel">
          <header><div><h3 data-role="session-title">Session details</h3><p data-role="session-meta">Select a session</p></div><span class="status-chip neutral" data-role="session-status">—</span></header>
          <div class="session-detail" data-role="session-detail"><div class="native-empty">No session selected</div></div>
        </section>
      </div>
    </section>`
    this.listen(root, "click", (event) => this.onClick(event))
    this.listen(root, "change", (event) => this.onChange(event))
    this.listen(root, "keydown", (event) => this.onKeyDown(event as KeyboardEvent))
    this.every(() => void this.refresh(), 5_000)
    void this.refresh()
  }

  async refresh(): Promise<void> {
    if (this.loading) return
    this.loading = true
    try {
      const payload = await this.context.api.get<LogicalSessionsPayload>("/logical-sessions")
      if (this.destroyed) return
      this.sessions = payload.sessions
      this.counts = payload.counts
      const visible = this.filteredSessions()
      if (!this.selectedId || !visible.some((session) => session.session_id === this.selectedId)) {
        this.selectedId = visible[0]?.session_id || null
        this.detail = null
      }
      this.renderSummary()
      this.renderList()
      void this.loadDetail()
    } catch (error) {
      if (!this.destroyed) this.context.notify(`Logical Sessions: ${error instanceof Error ? error.message : String(error)}`, "error")
    } finally {
      this.loading = false
    }
  }

  private filteredSessions(): LogicalSession[] {
    return this.filter === "all"
      ? this.sessions
      : this.sessions.filter((session) => session.status === this.filter)
  }

  private renderSummary(): void {
    const summary = this.root.querySelector<HTMLElement>("[data-role=sessions-summary]")
    if (!summary) return
    summary.innerHTML = [
      ["Active", this.counts.active, "accent"],
      ["Completed", this.counts.completed, "success"],
      ["Cancelled", this.counts.cancelled, this.counts.cancelled ? "warning" : "neutral"],
      ["Total", this.counts.total, "info"],
    ].map(([label, value, tone]) => `<article class="summary-card ${tone}"><span>${label}</span><strong>${value}</strong></article>`).join("")
  }

  private renderList(): void {
    const visible = this.filteredSessions()
    const count = this.root.querySelector<HTMLElement>("[data-role=sessions-count]")
    if (count) count.textContent = `${visible.length} shown · ${this.counts.total} total`
    const list = this.root.querySelector<HTMLElement>("[data-role=sessions-list]")
    if (!list) return
    if (!visible.length) {
      list.innerHTML = '<div class="native-empty"><strong>No logical sessions</strong><span>Change the status filter or create a session through session_manage.</span></div>'
      this.detail = null
      this.renderDetail()
      return
    }
    list.innerHTML = `<table class="native-table sessions-table" role="grid" aria-label="Logical Sessions"><thead><tr><th>Status</th><th>Label</th><th>Objective</th><th>Updated</th></tr></thead><tbody>${visible.map((session) => {
      const selected = session.session_id === this.selectedId
      return `<tr class="${selected ? "selected" : ""}" data-session-id="${escapeHtml(session.session_id)}" tabindex="${selected ? "0" : "-1"}" aria-selected="${selected}"><td><span class="status-chip ${sessionTone(session.status)}">${escapeHtml(session.status)}</span></td><td><strong>${escapeHtml(session.label || "Untitled session")}</strong><small>${escapeHtml(session.session_id)}</small></td><td>${escapeHtml(session.objective || "—")}</td><td>${formatAge(session.updated_at)}</td></tr>`
    }).join("")}</tbody></table>`
  }

  private async loadDetail(): Promise<void> {
    const sessionId = this.selectedId
    const request = ++this.detailRequest
    if (!sessionId) {
      this.detail = null
      this.renderDetail()
      return
    }
    if (this.detail?.session_id !== sessionId) {
      this.detail = null
      this.renderDetail(true)
    }
    try {
      const detail = await this.context.api.get<LogicalSession>(`/logical-sessions/detail${queryString({ session_id: sessionId })}`)
      if (this.destroyed || request !== this.detailRequest) return
      this.detail = detail
      this.renderDetail()
    } catch (error) {
      if (this.destroyed || request !== this.detailRequest) return
      this.context.notify(`Session detail: ${error instanceof Error ? error.message : String(error)}`, "error")
    }
  }

  private renderDetail(loading = false): void {
    const target = this.root.querySelector<HTMLElement>("[data-role=session-detail]")
    const title = this.root.querySelector<HTMLElement>("[data-role=session-title]")
    const meta = this.root.querySelector<HTMLElement>("[data-role=session-meta]")
    const status = this.root.querySelector<HTMLElement>("[data-role=session-status]")
    if (!target) return
    const session = this.detail
    if (!session) {
      if (title) title.textContent = "Session details"
      if (meta) meta.textContent = this.selectedId ? "Loading state…" : "Select a session"
      if (status) {
        status.className = "status-chip neutral"
        status.textContent = "—"
      }
      target.innerHTML = loading ? '<div class="native-loading">Loading session details…</div>' : '<div class="native-empty">No session selected</div>'
      return
    }
    if (title) title.textContent = session.label || "Untitled session"
    if (meta) meta.textContent = `${session.session_id} · updated ${formatAge(session.updated_at)}`
    if (status) {
      status.className = `status-chip ${sessionTone(session.status)}`
      status.textContent = session.status.toUpperCase()
    }
    const progress = session.progress
    const plan = session.plan
    const planHtml = plan ? `<section class="session-section"><div class="session-section-title"><h4>Plan</h4><span class="status-chip ${sessionTone(plan.status)}">${escapeHtml(plan.status)}</span></div><p class="session-plan-objective">${escapeHtml(plan.objective)}</p>${plan.note ? `<p class="session-note">${escapeHtml(plan.note)}</p>` : ""}<div class="session-plan-steps">${plan.steps.map((step) => `<article><span class="status-chip ${sessionTone(step.status)}">${escapeHtml(step.status)}</span><div><strong>${escapeHtml(step.text)}</strong><small>${escapeHtml(step.id)}${step.note ? ` · ${escapeHtml(step.note)}` : ""}</small></div></article>`).join("") || '<div class="native-empty">No plan steps</div>'}</div></section>` : '<section class="session-section"><div class="session-section-title"><h4>Plan</h4></div><div class="native-empty compact">No Goal/Plan attached</div></section>'
    const activityHtml = session.recent_activity.length ? session.recent_activity.slice().reverse().map((event) => `<article class="session-activity-row"><div><strong>${escapeHtml(event.type)}</strong><span>${escapeHtml(event.actor)} · ${formatAge(event.ts)}</span></div><pre>${highlightedHtml(JSON.stringify(event.data || {}, null, 2), "activity.json")}</pre></article>`).join("") : '<div class="native-empty compact">No activity recorded</div>'
    target.innerHTML = `<section class="session-identity"><dl class="detail-grid"><div><dt>Session ID</dt><dd><code>${escapeHtml(session.session_id)}</code></dd></div><div><dt>Created</dt><dd>${formatDate(session.created_at)}</dd></div><div><dt>Updated</dt><dd>${formatDate(session.updated_at)}</dd></div><div><dt>Status</dt><dd>${escapeHtml(session.status)}</dd></div></dl></section>${textBlock("Objective", session.objective)}<section class="session-section"><div class="session-section-title"><h4>Progress</h4><span>${progress.updated_at ? `Updated ${formatAge(progress.updated_at)}` : "No checkpoint timestamp"}</span></div><div class="session-progress-grid">${textBlock("Summary", progress.summary)}${textBlock("Next", progress.next)}${stringList("Findings", progress.findings || [])}${stringList("Blockers", progress.blockers || [])}</div></section>${planHtml}<section class="session-section"><div class="session-section-title"><h4>Recent activity</h4><span>${session.recent_activity.length} events</span></div><div class="session-activity">${activityHtml}</div></section>`
  }

  private selectSession(sessionId: string, focus = false): void {
    if (sessionId === this.selectedId && this.detail?.session_id === sessionId) return
    this.selectedId = sessionId
    this.detail = null
    this.renderList()
    void this.loadDetail()
    if (focus) this.root.querySelector<HTMLElement>(`[data-session-id="${CSS.escape(sessionId)}"]`)?.focus()
  }

  private onClick(event: MouseEvent): void {
    const sessionId = (event.target as HTMLElement).closest<HTMLElement>("[data-session-id]")?.dataset.sessionId
    if (sessionId) this.selectSession(sessionId)
  }

  private onChange(event: Event): void {
    const target = event.target
    if (!(target instanceof HTMLSelectElement) || target.dataset.filter !== "status") return
    if (!SESSION_STATUSES.includes(target.value as SessionFilter)) return
    this.filter = target.value as SessionFilter
    const visible = this.filteredSessions()
    if (!this.selectedId || !visible.some((session) => session.session_id === this.selectedId)) {
      this.selectedId = visible[0]?.session_id || null
      this.detail = null
    }
    this.renderList()
    void this.loadDetail()
  }

  private onKeyDown(event: KeyboardEvent): void {
    const row = (event.target as HTMLElement).closest<HTMLElement>("[data-session-id]")
    if (!row) return
    const visible = this.filteredSessions()
    const current = visible.findIndex((session) => session.session_id === row.dataset.sessionId)
    if (current < 0) return
    let next = current
    if (event.key === "ArrowDown") next = Math.min(visible.length - 1, current + 1)
    else if (event.key === "ArrowUp") next = Math.max(0, current - 1)
    else if (event.key === "Home") next = 0
    else if (event.key === "End") next = visible.length - 1
    else if (event.key !== "Enter" && event.key !== " ") return
    event.preventDefault()
    const session = visible[next]
    if (session) this.selectSession(session.session_id, true)
  }
}
