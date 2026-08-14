from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"expected patch context not found in {path}")
    p.write_text(text.replace(old, new, 1))


session_path = "src/local_shell_mcp/session_runtime.py"
old_finish = '''            if normalized_action == "finish":
                if logical.plan is not None and logical.plan.status in {"active", "blocked"}:
                    raise ValueError(
                        "Cannot finish a session while its plan is active or blocked; finish or cancel the plan first"
                    )
                logical.status = "completed"
                run.status = "completed"
                run.updated_at = time.time()
                logical.active_run_id = None
                self._attachments.pop(session_key, None)
                self._append_activity_locked(
                    logical,
                    "session.completed",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return self._public_state_locked(logical)

            if normalized_action == "cancel":
                logical.status = "cancelled"
                run.status = "cancelled"
                run.updated_at = time.time()
                logical.active_run_id = None
                if logical.plan is not None and logical.plan.status not in {"completed", "cancelled"}:
                    logical.plan.status = "cancelled"
                    logical.plan.updated_at = run.updated_at
                    logical.plan.continuation_pending = False
                    logical.plan.continuation_pending_since = None
                    logical.plan.continuation_claim_id = None
                self._attachments.pop(session_key, None)
                self._append_activity_locked(
                    logical,
                    "session.cancelled",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return self._public_state_locked(logical)
'''
new_finish = '''            if normalized_action in {"finish", "cancel"}:
                if (
                    normalized_action == "finish"
                    and logical.plan is not None
                    and logical.plan.status in {"active", "blocked"}
                ):
                    raise ValueError(
                        "Cannot finish a session while its plan is active or blocked; finish or cancel the plan first"
                    )
                snapshot = copy.deepcopy(logical)
                previous_attachment = self._attachments.get(session_key)
                try:
                    now = time.time()
                    logical.status = "completed" if normalized_action == "finish" else "cancelled"
                    run.status = logical.status
                    run.updated_at = now
                    logical.active_run_id = None
                    if (
                        normalized_action == "cancel"
                        and logical.plan is not None
                        and logical.plan.status not in {"completed", "cancelled"}
                    ):
                        logical.plan.status = "cancelled"
                        logical.plan.updated_at = now
                        logical.plan.continuation_pending = False
                        logical.plan.continuation_pending_since = None
                        logical.plan.continuation_claim_id = None
                    self._attachments.pop(session_key, None)
                    self._append_activity_locked(
                        logical,
                        "session.completed" if normalized_action == "finish" else "session.cancelled",
                        actor="agent",
                        data={"run_id": run.run_id},
                    )
                except Exception as exc:
                    self._sessions[snapshot.session_id] = snapshot
                    if previous_attachment is None:
                        self._attachments.pop(session_key, None)
                    else:
                        self._attachments[session_key] = previous_attachment
                    try:
                        self._save_locked(snapshot)
                    except Exception as rollback_exc:  # noqa: BLE001 - preserve original error.
                        exc.add_note(
                            "Session terminal rollback warning: "
                            f"{type(rollback_exc).__name__}: {rollback_exc}"
                        )
                    raise
                return self._public_state_locked(logical)
'''
replace_once(session_path, old_finish, new_finish)

ui_path = "ui/src/live-workspace.ts"
replace_once(
    ui_path,
    '  if (config) config.sessionId = String(payload.channel.session_id || config.sessionId || "")',
    '  if (config) config.sessionId = String(payload.channel.session_id ?? "")',
)
replace_once(
    ui_path,
    '    if (config) config.sessionId = String(payload.session_id || config.sessionId || "")',
    '    if (config) config.sessionId = String(payload.session_id ?? "")',
)

test_path = Path("tests/test_session_runtime.py")
test_text = test_path.read_text()
marker = "def test_terminal_transition_rolls_back_when_activity_persistence_fails"
if marker not in test_text:
    test_text += r'''

@pytest.mark.parametrize("action", ["finish", "cancel"])
def test_terminal_transition_rolls_back_when_activity_persistence_fails(
    tmp_path, monkeypatch, action
):
    state_dir = tmp_path / ".state"
    manager = SessionRuntimeManager(state_dir)
    started = manager.manage("mcp:agent", "user", action="start", objective="Task")
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    original_append = manager._append_activity_locked

    def fail_terminal_activity(session, event_type, **kwargs):
        if event_type in {"session.completed", "session.cancelled"}:
            raise OSError("simulated terminal activity persistence failure")
        return original_append(session, event_type, **kwargs)

    monkeypatch.setattr(manager, "_append_activity_locked", fail_terminal_activity)
    with pytest.raises(OSError, match="terminal activity persistence failure"):
        manager.manage(
            "mcp:agent",
            "user",
            action=action,
            session_id=session_id,
            session_run_id=run_id,
        )

    current = manager.manage("mcp:reader", "user", action="get", session_id=session_id)
    assert current["status"] == "active"
    assert current["active_run"]["run_id"] == run_id
    assert current["active_run"]["status"] == "active"
    assert manager.current_session_id("mcp:agent", subject="user") == session_id

    restored = SessionRuntimeManager(state_dir)
    durable = restored.manage("mcp:reader", "user", action="get", session_id=session_id)
    assert durable["status"] == "active"
    assert durable["active_run"]["run_id"] == run_id
    assert durable["active_run"]["status"] == "active"
'''
    test_path.write_text(test_text)
