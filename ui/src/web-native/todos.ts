import type { TodoItem, TodoPayload } from "../types"
import {
  BaseController,
  button,
  confirmDialog,
  escapeHtml,
  iconButton,
  isTypingTarget,
  openFormDialog,
  statusClass,
  type NativePageContext,
} from "./common"

const TODO_STATUS = ["pending", "in_progress", "completed"] as const
const TODO_PRIORITY = ["low", "medium", "high"] as const

export class TodosController extends BaseController {
  private payload: TodoPayload = { revision: 0, todos: [] }
  private filter: "all" | "open" | "completed" = "all"
  private selected = 0
  private saving = false

  mount(root: HTMLElement): void {
    this.root = root
    this.root.innerHTML = `<section class="native-page todos-page"><div class="todo-summary" data-role="todo-summary"></div><div class="native-toolbar"><div><strong>Todos</strong><span class="toolbar-detail">Persistent operational work shared with MCP</span></div><div class="toolbar-actions">${button("Add", "add", { icon: "+", primary: true })}${button("Edit", "edit", { disabled: true })}${button("Status", "status", { disabled: true })}${button("Priority", "priority", { disabled: true })}${button("Delete", "delete", { danger: true, disabled: true })}${iconButton("Refresh", "refresh", "↻")}</div></div><section class="native-panel todo-list-panel"><header><div><h3 data-role="todo-title">All todos</h3><p data-role="todo-count">Loading…</p></div><div class="todo-filters"><button type="button" data-todo-filter="all">All</button><button type="button" data-todo-filter="open">Open</button><button type="button" data-todo-filter="completed">Done</button></div></header><div class="todo-list-native" data-role="todo-list"><div class="native-loading">Loading todos…</div></div></section><footer class="shortcut-strip"><span><kbd>Enter</kbd> status</span><span><kbd>p</kbd> priority</span><span><kbd>n</kbd> add</span><span><kbd>e</kbd> edit</span><span><kbd>Del</kbd> delete</span><span><kbd>f</kbd> filter</span></footer></section>`
    this.listen(root, "click", (event) => this.onClick(event))
    this.listen(document, "keydown", (event) => this.onKeyDown(event as KeyboardEvent))
    void this.refresh()
  }

  private visible(): TodoItem[] {
    if (this.filter === "open") return this.payload.todos.filter((todo) => todo.status !== "completed")
    if (this.filter === "completed") return this.payload.todos.filter((todo) => todo.status === "completed")
    return this.payload.todos
  }

  private current(): TodoItem | undefined {
    return this.visible()[this.selected]
  }

  async refresh(): Promise<void> {
    if (this.saving) return
    try {
      this.payload = await this.context.api.get<TodoPayload>("/todos")
      this.selected = Math.min(this.selected, Math.max(0, this.visible().length - 1))
      this.render()
    } catch (error) {
      this.context.notify(`Todos: ${error instanceof Error ? error.message : String(error)}`, "error")
    }
  }

  private render(): void {
    const counts = { total: this.payload.todos.length, open: this.payload.todos.filter((todo) => todo.status !== "completed").length, completed: this.payload.todos.filter((todo) => todo.status === "completed").length }
    const summary = this.root.querySelector<HTMLElement>("[data-role=todo-summary]")
    if (summary) summary.innerHTML = [["All", counts.total, "accent", "all"], ["Open", counts.open, "warning", "open"], ["Done", counts.completed, "success", "completed"], ["View", this.filter.toUpperCase(), "info", this.filter]].map(([label, value, tone, filter]) => `<button type="button" class="summary-card ${tone} ${filter === this.filter ? "active" : ""}" data-todo-filter="${filter}"><span>${label}</span><strong>${value}</strong></button>`).join("")
    this.root.querySelectorAll<HTMLElement>("[data-todo-filter]").forEach((element) => element.classList.toggle("active", element.dataset.todoFilter === this.filter))
    const title = this.root.querySelector<HTMLElement>("[data-role=todo-title]")
    const count = this.root.querySelector<HTMLElement>("[data-role=todo-count]")
    if (title) title.textContent = this.filter === "all" ? "All todos" : this.filter === "open" ? "Open todos" : "Completed todos"
    if (count) count.textContent = `${this.visible().length} visible · revision ${this.payload.revision}${this.saving ? " · saving" : ""}`
    const list = this.root.querySelector<HTMLElement>("[data-role=todo-list]")
    const visible = this.visible()
    if (list) list.innerHTML = visible.length ? visible.map((todo, index) => `<button type="button" class="todo-native-row ${index === this.selected ? "selected" : ""} ${todo.status === "completed" ? "completed" : ""}" data-todo-index="${index}"><span class="todo-status ${statusClass(todo.status)}">${todo.status === "completed" ? "✓" : todo.status === "in_progress" ? "◐" : "○"}</span><span class="todo-content"><strong>${escapeHtml(todo.content)}</strong><small>${escapeHtml(todo.id)}</small></span><span class="priority-chip ${escapeHtml(todo.priority)}">${escapeHtml(todo.priority.toUpperCase())}</span></button>`).join("") : '<div class="native-empty"><strong>No matching todos</strong><span>Add an item or switch filters.</span></div>'
    const disabled = !this.current() || this.saving
    for (const action of ["edit", "status", "priority", "delete"]) {
      const element = this.root.querySelector<HTMLButtonElement>(`[data-action=${action}]`)
      if (element) element.disabled = disabled
    }
  }

  private async save(mutator: (todos: TodoItem[]) => TodoItem[], message: string): Promise<void> {
    if (this.saving) return
    this.saving = true
    this.render()
    try {
      let base = this.payload
      let next = mutator(base.todos)
      try {
        this.payload = await this.context.api.send<TodoPayload>("/todos", "PUT", { todos: next, expected_revision: base.revision })
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error)
        if (!detail.includes("changed from revision")) throw error
        base = await this.context.api.get<TodoPayload>("/todos")
        next = mutator(base.todos)
        this.payload = await this.context.api.send<TodoPayload>("/todos", "PUT", { todos: next, expected_revision: base.revision })
      }
      this.context.notify(message, "success")
      await this.context.refreshChrome()
    } catch (error) {
      this.context.notify(`Todos: ${error instanceof Error ? error.message : String(error)}`, "error")
    } finally {
      this.saving = false
      this.selected = Math.min(this.selected, Math.max(0, this.visible().length - 1))
      this.render()
    }
  }

  private async add(): Promise<void> {
    const values = await openFormDialog({ title: "Add todo", fields: [{ name: "content", label: "Work item", placeholder: "What needs to be done?", required: true }], submitLabel: "Add todo" })
    const content = values?.content.trim()
    if (!content) return
    const item: TodoItem = { id: `todo-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`, content, status: "pending", priority: "medium" }
    await this.save((todos) => [...todos, item], "Todo added")
  }

  private async edit(): Promise<void> {
    const current = this.current()
    if (!current) return
    const values = await openFormDialog({ title: "Edit todo", fields: [{ name: "content", label: "Work item", value: current.content, required: true }], submitLabel: "Save" })
    const content = values?.content.trim()
    if (!content) return
    await this.save((todos) => todos.map((todo) => todo.id === current.id ? { ...todo, content } : todo), "Todo updated")
  }

  private cycleStatus(): void {
    const current = this.current()
    if (!current) return
    const status = TODO_STATUS[(TODO_STATUS.indexOf(current.status as typeof TODO_STATUS[number]) + 1) % TODO_STATUS.length]
    void this.save((todos) => todos.map((todo) => todo.id === current.id ? { ...todo, status } : todo), `Status changed to ${status}`)
  }

  private cyclePriority(): void {
    const current = this.current()
    if (!current) return
    const priority = TODO_PRIORITY[(TODO_PRIORITY.indexOf(current.priority as typeof TODO_PRIORITY[number]) + 1) % TODO_PRIORITY.length]
    void this.save((todos) => todos.map((todo) => todo.id === current.id ? { ...todo, priority } : todo), `Priority changed to ${priority}`)
  }

  private async delete(): Promise<void> {
    const current = this.current()
    if (!current || !await confirmDialog("Delete todo?", current.content, "Delete")) return
    await this.save((todos) => todos.filter((todo) => todo.id !== current.id), "Todo deleted")
  }

  private setFilter(filter: "all" | "open" | "completed"): void {
    this.filter = filter
    this.selected = 0
    this.render()
  }

  private onClick(event: MouseEvent): void {
    const target = event.target as HTMLElement
    const index = target.closest<HTMLElement>("[data-todo-index]")?.dataset.todoIndex
    if (index !== undefined) {
      this.selected = Number(index)
      this.render()
      return
    }
    const filter = target.closest<HTMLElement>("[data-todo-filter]")?.dataset.todoFilter
    if (filter === "all" || filter === "open" || filter === "completed") {
      this.setFilter(filter)
      return
    }
    const action = target.closest<HTMLElement>("[data-action]")?.dataset.action
    if (action === "add") void this.add()
    else if (action === "edit") void this.edit()
    else if (action === "status") this.cycleStatus()
    else if (action === "priority") this.cyclePriority()
    else if (action === "delete") void this.delete()
    else if (action === "refresh") void this.refresh()
  }

  private onKeyDown(event: KeyboardEvent): void {
    if (!this.root.isConnected || isTypingTarget(event.target)) return
    const visible = this.visible()
    if (event.key === "ArrowDown" || event.key.toLowerCase() === "j") {
      event.preventDefault(); this.selected = Math.min(visible.length - 1, this.selected + 1); this.render()
    } else if (event.key === "ArrowUp" || event.key.toLowerCase() === "k") {
      event.preventDefault(); this.selected = Math.max(0, this.selected - 1); this.render()
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault(); this.cycleStatus()
    } else if (event.key.toLowerCase() === "p") this.cyclePriority()
    else if (event.key.toLowerCase() === "n") void this.add()
    else if (event.key.toLowerCase() === "e") void this.edit()
    else if (event.key === "Delete") void this.delete()
    else if (event.key.toLowerCase() === "f") this.setFilter(this.filter === "all" ? "open" : this.filter === "open" ? "completed" : "all")
    else if (event.key.toLowerCase() === "r") void this.refresh()
  }
}

