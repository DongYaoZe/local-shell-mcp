from __future__ import annotations

import json
import threading
import time

from .settings import get_settings
from .state_store import get_state_store

_TODO_LOCK = threading.Lock()


class TodoConflictError(RuntimeError):
    pass


def todo_read() -> dict:
    raw = get_state_store().read_bytes("todos.json")
    if raw is None:
        return {"revision": 0, "updated_at": None, "todos": []}
    settings = get_settings()
    size = len(raw)
    if size > settings.max_todo_bytes:
        raise ValueError(f"Refusing to read {size} todo bytes; max is {settings.max_todo_bytes}")
    return json.loads(raw.decode("utf-8"))


def todo_write(todos: list[dict], expected_revision: int | None = None) -> dict:
    settings = get_settings()
    if len(todos) > settings.max_todos:
        raise ValueError(f"Refusing to write {len(todos)} todos; max is {settings.max_todos}")
    normalized = []
    for idx, item in enumerate(todos):
        normalized.append(
            {
                "id": str(item.get("id") or idx + 1),
                "content": str(item.get("content") or ""),
                "status": str(item.get("status") or "pending"),
                "priority": str(item.get("priority") or "medium"),
            }
        )

    with _TODO_LOCK:
        current = todo_read()
        current_revision = int(current.get("revision") or 0)
        if expected_revision is not None and expected_revision != current_revision:
            raise TodoConflictError(
                f"Todo list changed from revision {expected_revision} to {current_revision}; reload before saving"
            )
        payload = {
            "revision": current_revision + 1,
            "updated_at": time.time(),
            "todos": normalized,
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2)
        encoded_bytes = len(encoded.encode("utf-8"))
        if encoded_bytes > settings.max_todo_bytes:
            raise ValueError(f"Refusing to write {encoded_bytes} todo bytes; max is {settings.max_todo_bytes}")
        get_state_store().write_bytes("todos.json", encoded.encode("utf-8"))
        return payload
