import { describe, expect, test } from "bun:test"
import type { TodoPayload } from "../types"
import type { NativePageContext } from "./common"
import { TodosController } from "./todos"

describe("Native WebUI todo mutations", () => {
  test("queues rapid mutations and applies each to the latest revision", async () => {
    const requests: Array<{ body: Record<string, unknown>; resolve: (payload: TodoPayload) => void }> = []
    const context: NativePageContext = {
      api: {
        get: async () => ({ revision: 0, todos: [] }) as never,
        send: async (_path, _method, body) => new Promise<TodoPayload>((resolve) => requests.push({ body, resolve })) as never,
      },
      uiPath: "/ui",
      accessToken: () => null,
      machines: () => [],
      notify: () => undefined,
      refreshChrome: async () => undefined,
    }
    const controller = new TodosController(context) as unknown as {
      payload: TodoPayload
      render: () => void
      save: (mutator: (todos: TodoPayload["todos"]) => TodoPayload["todos"], message: string) => Promise<void>
    }
    controller.payload = {
      revision: 0,
      todos: [{ id: "todo-1", content: "work", status: "pending", priority: "low" }],
    }
    controller.render = () => undefined

    const statusSave = controller.save(
      (todos) => todos.map((todo) => todo.id === "todo-1" ? { ...todo, status: "in_progress" } : todo),
      "status",
    )
    const prioritySave = controller.save(
      (todos) => todos.map((todo) => todo.id === "todo-1" ? { ...todo, priority: "medium" } : todo),
      "priority",
    )

    await Promise.resolve()
    expect(requests).toHaveLength(1)
    requests[0]!.resolve({ revision: 1, todos: requests[0]!.body.todos as TodoPayload["todos"] })
    for (let attempt = 0; attempt < 10 && requests.length < 2; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 0))
    }
    expect(requests).toHaveLength(2)
    expect(requests[1]!.body).toMatchObject({
      expected_revision: 1,
      todos: [{ id: "todo-1", status: "in_progress", priority: "medium" }],
    })
    requests[1]!.resolve({ revision: 2, todos: requests[1]!.body.todos as TodoPayload["todos"] })

    await Promise.all([statusSave, prioritySave])
    expect(controller.payload.revision).toBe(2)
  })
})
