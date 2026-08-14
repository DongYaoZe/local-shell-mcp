from __future__ import annotations

import threading
import time

import pytest

from local_shell_mcp.live_channel import LiveChannelManager
from local_shell_mcp.oauth import ALL_OAUTH_SCOPES
from local_shell_mcp.session_runtime import (
    PLAN_CONTINUATION_FAILURE_BACKOFF_S,
    PLAN_EXECUTION_LEASE_S,
    PLAN_MAX_STEPS,
    PLAN_NOTE_LIMIT,
    PLAN_OBJECTIVE_LIMIT,
    PLAN_STEP_ID_LIMIT,
    PLAN_STEP_TEXT_LIMIT,
    SESSION_RUN_HISTORY_LIMIT,
    SessionRuntimeManager,
)
from local_shell_mcp.settings import get_settings
from local_shell_mcp.state_store import MemoryStateStore, clear_memory_state


def test_session_progress_and_plan_survive_manager_reload(tmp_path):
    state_dir = tmp_path / ".state"
    manager = SessionRuntimeManager(state_dir)
    started = manager.manage(
        "mcp:first",
        "user",
        action="start",
        label="PR work",
        objective="Implement durable logical sessions",
    )
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    manager.manage(
        "mcp:first",
        "user",
        action="report",
        session_run_id=run_id,
        summary="Runtime is implemented",
        findings=["Live channels must not own plans"],
        next="Run integration tests",
        blockers=[],
    )
    manager.manage_plan(
        "mcp:first",
        action="start",
        session_run_id=run_id,
        objective="Ship the change",
        steps=[{"id": "test", "text": "Run tests"}],
    )

    restored = SessionRuntimeManager(state_dir)
    state = restored.manage(
        "mcp:reader", "user", action="get", session_id=session_id
    )

    assert state["label"] == "PR work"
    assert state["objective"] == "Implement durable logical sessions"
    assert state["progress"]["summary"] == "Runtime is implemented"
    assert state["progress"]["findings"] == ["Live channels must not own plans"]
    assert state["plan"]["objective"] == "Ship the change"
    assert any(event["type"] == "session.reported" for event in state["recent_activity"])


def test_resume_takeover_supersedes_previous_agent_run(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage(
        "mcp:agent-a", "user", action="start", objective="Long-running task"
    )
    session_id = started["session_id"]
    first_run_id = started["active_run"]["run_id"]

    with pytest.raises(ValueError, match="takeover=true"):
        manager.manage(
            "mcp:agent-b", "user", action="resume", session_id=session_id
        )

    resumed = manager.manage(
        "mcp:agent-b",
        "user",
        action="resume",
        session_id=session_id,
        takeover=True,
    )
    assert resumed["active_run"]["run_id"] != first_run_id
    assert next(run for run in resumed["runs"] if run["run_id"] == first_run_id)["status"] == (
        "superseded"
    )

    with pytest.raises(RuntimeError, match="superseded"):
        manager.begin_tool_call(
            "mcp:agent-a", "stale", expected_run_id=first_run_id
        )

    second_run_id = resumed["active_run"]["run_id"]
    lease = manager.begin_tool_call(
        "mcp:agent-b", "current", expected_run_id=second_run_id
    )
    assert manager.finish_tool_call(lease, "tool.completed") is None
    reported = manager.manage(
        "mcp:agent-b",
        "user",
        action="report",
        session_id=session_id,
        session_run_id=second_run_id,
        summary="Agent B took over",
    )
    assert reported["progress"]["summary"] == "Agent B took over"


def test_takeover_on_same_transport_creates_new_run_lease(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:same", "user", action="start", objective="Task")
    session_id = started["session_id"]
    first_run_id = started["active_run"]["run_id"]

    resumed = manager.manage(
        "mcp:same",
        "user",
        action="resume",
        session_id=session_id,
        takeover=True,
    )
    second_run_id = resumed["active_run"]["run_id"]

    assert second_run_id != first_run_id
    assert next(run for run in resumed["runs"] if run["run_id"] == first_run_id)["status"] == (
        "superseded"
    )
    with pytest.raises(RuntimeError, match="superseded"):
        manager.begin_tool_call(
            "mcp:same", "stale", expected_run_id=first_run_id
        )
    lease = manager.begin_tool_call(
        "mcp:same", "current", expected_run_id=second_run_id
    )
    assert manager.finish_tool_call(lease, "tool.completed") is None


def test_session_list_compacts_large_progress(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    run_id = started["active_run"]["run_id"]
    manager.manage(
        "mcp:a",
        "user",
        action="report",
        session_run_id=run_id,
        summary="s" * 2000,
        findings=["f" * 2000] * 50,
        next="n" * 2000,
        blockers=["b" * 2000] * 50,
    )

    progress = manager.manage("mcp:reader", "user", action="list")["sessions"][0][
        "progress"
    ]
    assert set(progress) == {
        "summary",
        "next",
        "finding_count",
        "blocker_count",
        "updated_at",
    }
    assert len(progress["summary"]) == 500
    assert len(progress["next"]) == 500
    assert progress["finding_count"] == 50
    assert progress["blocker_count"] == 50


def test_plan_fields_are_bounded_before_persistence(tmp_path):
    state_dir = tmp_path / ".state"
    manager = SessionRuntimeManager(state_dir)
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    run_id = started["active_run"]["run_id"]
    oversized_id = "i" * (PLAN_STEP_ID_LIMIT + 200)
    plan = manager.manage_plan(
        "mcp:a",
        action="start",
        session_run_id=run_id,
        objective="o" * (PLAN_OBJECTIVE_LIMIT + 200),
        steps=[
            {
                "id": oversized_id,
                "text": "t" * (PLAN_STEP_TEXT_LIMIT + 200),
                "note": "n" * (PLAN_NOTE_LIMIT + 200),
            }
        ],
    )["plan"]

    assert len(plan["objective"]) == PLAN_OBJECTIVE_LIMIT
    assert len(plan["steps"][0]["id"]) == PLAN_STEP_ID_LIMIT
    assert len(plan["steps"][0]["text"]) == PLAN_STEP_TEXT_LIMIT
    assert len(plan["steps"][0]["note"]) == PLAN_NOTE_LIMIT

    updated = manager.manage_plan(
        "mcp:a",
        action="update",
        session_run_id=run_id,
        objective="u" * (PLAN_OBJECTIVE_LIMIT + 200),
        step_id=oversized_id,
        text="x" * (PLAN_STEP_TEXT_LIMIT + 200),
        note="y" * (PLAN_NOTE_LIMIT + 200),
    )["plan"]
    assert len(updated["objective"]) == PLAN_OBJECTIVE_LIMIT
    assert len(updated["steps"][0]["text"]) == PLAN_STEP_TEXT_LIMIT
    assert len(updated["steps"][0]["note"]) == PLAN_NOTE_LIMIT

    blocked = manager.manage_plan(
        "mcp:a",
        action="block",
        session_run_id=run_id,
        note="b" * (PLAN_NOTE_LIMIT + 200),
    )["plan"]
    assert len(blocked["note"]) == PLAN_NOTE_LIMIT
    manager.manage_plan("mcp:a", action="resume", session_run_id=run_id)
    manager.manage_plan(
        "mcp:a",
        action="update",
        session_run_id=run_id,
        step_id=oversized_id,
        status="completed",
    )
    finished = manager.manage_plan(
        "mcp:a",
        action="finish",
        session_run_id=run_id,
        note="f" * (PLAN_NOTE_LIMIT + 200),
    )["plan"]
    assert len(finished["note"]) == PLAN_NOTE_LIMIT

    restored = SessionRuntimeManager(state_dir).manage(
        "mcp:reader", "user", action="get", session_id=started["session_id"]
    )["plan"]
    assert len(restored["objective"]) == PLAN_OBJECTIVE_LIMIT
    assert len(restored["steps"][0]["id"]) == PLAN_STEP_ID_LIMIT
    assert len(restored["steps"][0]["text"]) == PLAN_STEP_TEXT_LIMIT
    assert len(restored["steps"][0]["note"]) == PLAN_NOTE_LIMIT


def test_plan_continuation_waits_for_inflight_and_backs_off(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    manager.manage_plan(
        "mcp:a",
        action="start",
        session_run_id=run_id,
        objective="Task",
        steps=[{"id": "work", "text": "Work"}],
    )

    lease = manager.begin_tool_call(
        "mcp:a", "call-1", expected_run_id=run_id, data={"tool": "remote_transfer"}
    )
    logical = manager._sessions[session_id]
    assert logical.plan is not None
    logical.plan.last_agent_activity = time.time() - PLAN_EXECUTION_LEASE_S - 1
    assert manager.claim_plan_continuation(session_id, subject="user") is None

    assert manager.finish_tool_call(lease, "tool.completed", data={"ok": True}) is None
    logical.plan.last_agent_activity = time.time() - PLAN_EXECUTION_LEASE_S - 1
    claimed = manager.claim_plan_continuation(session_id, subject="user")
    assert claimed is not None
    failed = manager.report_plan_continuation(
        session_id, accepted=False, error="host unavailable", subject="user"
    )
    assert failed["continuation_count"] == 1
    assert failed["continuation_retry_after"] is not None
    assert failed["continuation_retry_after"] >= time.time() + PLAN_CONTINUATION_FAILURE_BACKOFF_S - 1
    logical.plan.last_agent_activity = time.time() - PLAN_EXECUTION_LEASE_S - 1
    assert manager.claim_plan_continuation(session_id, subject="user") is None
    logical.plan.continuation_retry_after = time.time() - 1
    assert manager.claim_plan_continuation(session_id, subject="user") is not None


def test_session_activity_persistence_failure_keeps_tool_lease_recoverable(
    tmp_path, monkeypatch
):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    run_id = started["active_run"]["run_id"]

    def fail_save(_session):
        raise OSError("disk full")

    monkeypatch.setattr(manager, "_save_locked", fail_save)
    lease = manager.begin_tool_call("mcp:a", "call-1", expected_run_id=run_id)
    assert lease is not None
    assert "disk full" in lease["persistence_error"]
    error = manager.finish_tool_call(lease, "tool.completed", data={"ok": True})
    assert error is not None and "disk full" in error


def test_sessions_use_configured_stateless_state_backend(tmp_path, monkeypatch):
    clear_memory_state()
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND", "memory")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", "session-runtime-test")
    get_settings.cache_clear()
    try:
        manager = SessionRuntimeManager()
        started = manager.manage("mcp:a", "user", action="start", objective="Task")
        restored = SessionRuntimeManager().manage(
            "mcp:reader", "user", action="get", session_id=started["session_id"]
        )
        assert restored["objective"] == "Task"
        assert not (tmp_path / ".state" / "sessions").exists()
    finally:
        get_settings.cache_clear()
        clear_memory_state()


def test_shared_backend_refreshes_sessions_across_controller_instances(tmp_path, monkeypatch):
    clear_memory_state()
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND", "redis")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_URL", "redis://state.test/0")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", "shared-session-runtime-test")
    get_settings.cache_clear()
    shared_store = MemoryStateStore("shared-session-runtime-test")
    monkeypatch.setattr(
        "local_shell_mcp.session_runtime.get_state_store", lambda: shared_store
    )
    try:
        first = SessionRuntimeManager()
        second = SessionRuntimeManager()
        assert second.manage("mcp:reader", "user", action="list")["sessions"] == []

        started = first.manage("mcp:first", "user", action="start", objective="Shared task")
        session_id = started["session_id"]
        first_run_id = started["active_run"]["run_id"]
        assert second.manage(
            "mcp:reader", "user", action="get", session_id=session_id
        )["objective"] == "Shared task"

        resumed = second.manage(
            "mcp:second",
            "user",
            action="resume",
            session_id=session_id,
            takeover=True,
        )
        second_run_id = resumed["active_run"]["run_id"]
        with pytest.raises(RuntimeError, match="superseded"):
            first.manage(
                "mcp:first",
                "user",
                action="report",
                session_id=session_id,
                session_run_id=first_run_id,
                summary="stale overwrite",
            )

        second.manage(
            "mcp:second",
            "user",
            action="report",
            session_id=session_id,
            session_run_id=second_run_id,
            summary="fresh state",
        )
        refreshed = first.manage(
            "mcp:reader-a", "user", action="get", session_id=session_id
        )
        assert refreshed["progress"]["summary"] == "fresh state"
        assert first.manage("mcp:list-a", "user", action="list")["sessions"][0][
            "session_id"
        ] == session_id
    finally:
        get_settings.cache_clear()
        clear_memory_state()


def test_shared_backend_refresh_preserves_local_run_owner(tmp_path, monkeypatch):
    clear_memory_state()
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND", "redis")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_URL", "redis://state.test/0")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", "session-owner-refresh-test")
    get_settings.cache_clear()
    shared_store = MemoryStateStore("session-owner-refresh-test")
    monkeypatch.setattr(
        "local_shell_mcp.session_runtime.get_state_store", lambda: shared_store
    )
    try:
        manager = SessionRuntimeManager()
        started = manager.manage("mcp:a", "user", action="start", objective="Task")
        session_id = started["session_id"]
        run_id = started["active_run"]["run_id"]
        assert manager.manage("mcp:list", "user", action="list")["sessions"][0][
            "session_id"
        ] == session_id

        resumed = manager.manage(
            "mcp:a",
            "user",
            action="resume",
            session_id=session_id,
            takeover=False,
        )

        assert resumed["active_run"]["run_id"] == run_id
        assert manager._sessions[session_id].active_run().session_key == "mcp:a"
    finally:
        get_settings.cache_clear()
        clear_memory_state()


def test_shared_backend_serializes_session_mutations_across_controllers(tmp_path, monkeypatch):
    clear_memory_state()
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND", "redis")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_URL", "redis://state.test/0")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", "session-rmw-lock-test")
    get_settings.cache_clear()
    shared_store = MemoryStateStore("session-rmw-lock-test")
    monkeypatch.setattr(
        "local_shell_mcp.session_runtime.get_state_store", lambda: shared_store
    )
    try:
        first = SessionRuntimeManager()
        second = SessionRuntimeManager()
        started = first.manage("mcp:first", "user", action="start", objective="Shared task")
        session_id = started["session_id"]
        run_id = started["active_run"]["run_id"]
        first.manage_plan(
            "mcp:first",
            action="start",
            session_run_id=run_id,
            objective="Shared task",
            steps=[{"id": "work", "text": "Work"}],
        )

        save_started = threading.Event()
        release_save = threading.Event()
        original_save = first._save_locked

        def pause_report_save(session):
            if threading.current_thread().name == "session-report":
                save_started.set()
                assert release_save.wait(2)
            original_save(session)

        monkeypatch.setattr(first, "_save_locked", pause_report_save)
        errors: list[BaseException] = []

        def report_progress() -> None:
            try:
                first.manage(
                    "mcp:first",
                    "user",
                    action="report",
                    session_run_id=run_id,
                    summary="report survives",
                )
            except BaseException as exc:  # pragma: no cover - asserted below.
                errors.append(exc)

        def block_plan() -> None:
            try:
                second.manage_plan_for_session(
                    session_id,
                    action="block",
                    note="needs input",
                    subject="user",
                )
            except BaseException as exc:  # pragma: no cover - asserted below.
                errors.append(exc)

        reporter = threading.Thread(target=report_progress, name="session-report")
        blocker = threading.Thread(target=block_plan, name="session-block")
        reporter.start()
        assert save_started.wait(1)
        blocker.start()
        time.sleep(0.1)
        release_save.set()
        reporter.join(2)
        blocker.join(2)

        assert not reporter.is_alive()
        assert not blocker.is_alive()
        assert errors == []
        restored = SessionRuntimeManager().get(session_id, subject="user")
        assert restored["progress"]["summary"] == "report survives"
        assert restored["plan"]["status"] == "blocked"
        assert restored["plan"]["note"] == "needs input"
    finally:
        get_settings.cache_clear()
        clear_memory_state()


def test_shared_backend_takeover_waits_for_remote_inflight_tool(tmp_path, monkeypatch):
    clear_memory_state()
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND", "redis")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_URL", "redis://state.test/0")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", "session-inflight-test")
    get_settings.cache_clear()
    shared_store = MemoryStateStore("session-inflight-test")
    monkeypatch.setattr(
        "local_shell_mcp.session_runtime.get_state_store", lambda: shared_store
    )
    try:
        first = SessionRuntimeManager()
        second = SessionRuntimeManager()
        started = first.manage("mcp:first", "user", action="start", objective="Shared task")
        session_id = started["session_id"]
        run_id = started["active_run"]["run_id"]
        lease = first.begin_tool_call(
            "mcp:first",
            "remote-call",
            expected_run_id=run_id,
            data={"tool": "remote_transfer"},
        )

        with pytest.raises(ValueError, match="tool calls are still in flight"):
            second.manage(
                "mcp:second",
                "user",
                action="resume",
                session_id=session_id,
                takeover=True,
            )

        assert first.finish_tool_call(lease, "tool.completed") is None
        resumed = second.manage(
            "mcp:second",
            "user",
            action="resume",
            session_id=session_id,
            takeover=True,
        )
        assert resumed["active_run"]["run_id"] != run_id
    finally:
        get_settings.cache_clear()
        clear_memory_state()


def test_session_access_is_scoped_to_principal(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "alice", action="start", objective="Private task")

    with pytest.raises(PermissionError, match="different principal"):
        manager.manage(
            "mcp:b", "bob", action="get", session_id=started["session_id"]
        )


def test_current_attachment_is_discarded_when_principal_changes(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "alice", action="start", objective="Private task")

    assert manager.current_session_id("mcp:a", subject="alice") == started["session_id"]
    assert manager.current_session_id("mcp:a", subject="bob") is None
    assert "mcp:a" not in manager._attachments


def test_session_initial_load_retries_after_transient_scan_failure(tmp_path, monkeypatch):
    state_dir = tmp_path / ".state"
    seeded = SessionRuntimeManager(state_dir).manage(
        "mcp:seed", "user", action="start", objective="Persisted"
    )
    manager = SessionRuntimeManager(state_dir)
    store = manager._state_store()

    class FlakyStore:
        def __init__(self, delegate):
            self.delegate = delegate
            self.failed = False

        def list_keys(self, prefix=""):
            if not self.failed:
                self.failed = True
                raise OSError("mount unavailable")
            return self.delegate.list_keys(prefix)

        def read_bytes(self, key):
            return self.delegate.read_bytes(key)

        def write_bytes(self, key, value):
            return self.delegate.write_bytes(key, value)

        def delete(self, key):
            return self.delegate.delete(key)

        def lock(self, key):
            return self.delegate.lock(key)

    flaky = FlakyStore(store)
    monkeypatch.setattr(manager, "_state_store", lambda: flaky)

    with pytest.raises(OSError, match="mount unavailable"):
        manager.get(seeded["session_id"], subject="user")
    assert manager._loaded_storage is None
    restored = manager.get(seeded["session_id"], subject="user")
    assert restored["objective"] == "Persisted"


def test_agent_run_history_is_bounded_and_keeps_active_run(tmp_path):
    state_dir = tmp_path / ".state"
    manager = SessionRuntimeManager(state_dir)
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    session_id = started["session_id"]
    active_run_id = started["active_run"]["run_id"]

    for _ in range(SESSION_RUN_HISTORY_LIMIT + 20):
        resumed = manager.manage(
            "mcp:a",
            "user",
            action="resume",
            session_id=session_id,
            takeover=True,
        )
        active_run_id = resumed["active_run"]["run_id"]

    logical = manager._sessions[session_id]
    assert len(logical.runs) == SESSION_RUN_HISTORY_LIMIT
    assert logical.active_run_id == active_run_id
    assert logical.active_run() is logical.runs[-1]

    restored_manager = SessionRuntimeManager(state_dir)
    restored_manager.get(session_id, subject="user")
    restored = restored_manager._sessions[session_id]
    assert len(restored.runs) == SESSION_RUN_HISTORY_LIMIT
    assert restored.active_run_id == active_run_id
    assert restored.active_run() is not None


def test_live_workspace_reuses_channel_for_resumed_logical_session(tmp_path):
    sessions = SessionRuntimeManager(tmp_path / ".state")
    logical = sessions.manage(
        "mcp:agent-a", "user", action="start", objective="Shared task"
    )
    session_id = logical["session_id"]
    live = LiveChannelManager()
    first, _ = live.open(
        session_key="mcp:agent-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=session_id,
    )

    sessions.manage(
        "mcp:agent-b",
        "user",
        action="resume",
        session_id=session_id,
        takeover=True,
    )
    second = live.bind_logical_session("mcp:agent-b", session_id)

    assert second is first
    assert second.logical_session_id == session_id
    assert live.active_for_session("mcp:agent-b") is first


def test_session_finish_requires_terminal_plan(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    run_id = started["active_run"]["run_id"]
    manager.manage_plan(
        "mcp:a",
        action="start",
        session_run_id=run_id,
        objective="Task",
        steps=[{"id": "work", "text": "Work"}],
    )

    with pytest.raises(ValueError, match="plan is active or blocked"):
        manager.manage("mcp:a", "user", action="finish", session_run_id=run_id)

    manager.manage_plan(
        "mcp:a", action="update", session_run_id=run_id, step_id="work", status="completed"
    )
    manager.manage_plan("mcp:a", action="finish", session_run_id=run_id)
    finished = manager.manage(
        "mcp:a", "user", action="finish", session_run_id=run_id
    )
    assert finished["status"] == "completed"
    assert finished["active_run"] is None


def test_session_runtime_validation_and_attachment_edges(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")

    assert manager.current_session_id("missing") is None
    assert manager.plan_state(None) is None
    assert manager.begin_tool_call("missing", "call", expected_run_id=None) is None
    assert manager.finish_tool_call(None, "tool.completed") is None
    with pytest.raises(ValueError, match="No logical session is attached"):
        manager.manage("missing", "user", action="get")
    with pytest.raises(ValueError, match="Unknown logical session"):
        manager.get("s_missing")

    first = manager.manage(
        "mcp:a",
        "user",
        action="start",
        label="  label  ",
        objective="  objective  ",
    )
    first_id = first["session_id"]
    first_run = first["active_run"]["run_id"]
    assert first["label"] == "label"
    assert first["objective"] == "objective"
    assert manager.current_session_id("mcp:a") == first_id
    assert manager.plan_state(first_id) is None

    with pytest.raises(RuntimeError, match="session_run_id is required"):
        manager.begin_tool_call("mcp:a", "missing-token", expected_run_id=None)

    second = manager.manage("mcp:a", "user", action="start", objective="second")
    second_id = second["session_id"]
    second_run = second["active_run"]["run_id"]
    detached = manager.get(first_id)
    assert detached["active_run"] is None
    assert detached["runs"][-1]["status"] == "detached"

    with pytest.raises(RuntimeError, match="different logical session"):
        manager._assert_attachment_locked("mcp:a", first_id)
    with pytest.raises(RuntimeError, match="superseded"):
        manager.begin_tool_call("mcp:a", "old-token", expected_run_id=first_run)

    manager._sessions[second_id].status = "cancelled"
    with pytest.raises(RuntimeError, match="cancelled"):
        manager._assert_attachment_locked("mcp:a")
    manager._sessions[second_id].status = "active"
    manager._sessions[second_id].runs[-1].status = "completed"
    with pytest.raises(RuntimeError, match="no longer active"):
        manager._assert_attachment_locked("mcp:a")
    manager._sessions[second_id].runs[-1].status = "active"

    lease = manager.begin_tool_call(
        "mcp:a", "stale-finish", expected_run_id=second_run
    )
    with pytest.raises(ValueError, match="tool calls are still in flight"):
        manager.manage(
            "mcp:a", "user", action="resume", session_id=second_id, takeover=True
        )
    assert manager.finish_tool_call(lease, "tool.completed") is None
    assert manager.get(second_id)["recent_activity"][-1]["data"]["stale_run"] is False
    takeover = manager.manage(
        "mcp:a", "user", action="resume", session_id=second_id, takeover=True
    )
    assert takeover["active_run"]["run_id"] != second_run

    assert manager.finish_tool_call(
        {"session_id": "missing", "run_id": "missing", "call_id": "missing"},
        "tool.completed",
    ) is None

    current_run = takeover["active_run"]["run_id"]
    report = manager.manage(
        "mcp:a",
        "user",
        action="report",
        session_id=second_id,
        session_run_id=current_run,
        require_run_token=True,
        findings=["finding", "  "],
        blockers=["blocker"],
        objective="updated objective",
        label="updated label",
    )
    assert report["progress"]["findings"] == ["finding"]
    assert report["progress"]["blockers"] == ["blocker"]
    assert report["objective"] == "updated objective"
    assert report["label"] == "updated label"
    with pytest.raises(ValueError, match="action=report requires"):
        manager.manage(
            "mcp:a",
            "user",
            action="report",
            session_id=second_id,
            session_run_id=current_run,
            require_run_token=True,
        )
    with pytest.raises(ValueError, match="action must be one of"):
        manager.manage(
            "mcp:a",
            "user",
            action="unknown",
            session_id=second_id,
            session_run_id=current_run,
            require_run_token=True,
        )


def test_plan_validation_update_and_terminal_edges(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:plan", "user", action="start")
    session_id = started["session_id"]

    assert manager.manage_plan("mcp:plan", action="get")["plan"] is None
    with pytest.raises(ValueError, match="objective is required"):
        manager.manage_plan("mcp:plan", action="start", objective=" ", steps=[])
    with pytest.raises(ValueError, match="at least one step"):
        manager.manage_plan("mcp:plan", action="start", objective="Goal", steps=[])
    with pytest.raises(ValueError, match="at most"):
        manager._normalize_plan_steps(
            [{"text": str(index)} for index in range(PLAN_MAX_STEPS + 1)]
        )
    with pytest.raises(ValueError, match="unique"):
        manager._normalize_plan_steps(
            [{"id": "same", "text": "one"}, {"id": "same", "text": "two"}]
        )
    with pytest.raises(ValueError, match="has no text"):
        manager._normalize_plan_steps([{"id": "blank", "text": " "}])
    with pytest.raises(ValueError, match="Unsupported plan step status"):
        manager._normalize_plan_steps([{"text": "work", "status": "weird"}])
    with pytest.raises(ValueError, match="at most one active"):
        manager._normalize_plan_steps(
            [
                {"text": "one", "status": "active"},
                {"text": "two", "status": "active"},
            ]
        )

    plan = manager.manage_plan(
        "mcp:plan",
        action="start",
        objective="Goal",
        steps=[
            {"id": "a", "text": "A", "note": "note"},
            {"id": "b", "text": "B"},
        ],
    )
    assert plan["plan"]["steps"][0]["note"] == "note"
    with pytest.raises(ValueError, match="already active"):
        manager.manage_plan(
            "mcp:plan", action="start", objective="Again", steps=[{"text": "x"}]
        )

    with pytest.raises(ValueError, match="objective cannot be empty"):
        manager.manage_plan("mcp:plan", action="update", objective=" ")
    with pytest.raises(ValueError, match="Unknown plan step"):
        manager.manage_plan("mcp:plan", action="update", step_id="missing", status="completed")
    with pytest.raises(ValueError, match="Unsupported plan step status"):
        manager.manage_plan("mcp:plan", action="update", step_id="a", status="weird")
    with pytest.raises(ValueError, match="step text cannot be empty"):
        manager.manage_plan("mcp:plan", action="update", step_id="a", text=" ")
    with pytest.raises(ValueError, match="step_id is required"):
        manager.manage_plan("mcp:plan", action="update", status="completed")
    with pytest.raises(ValueError, match="action=update requires"):
        manager.manage_plan("mcp:plan", action="update")

    updated = manager.manage_plan(
        "mcp:plan",
        action="update",
        objective="Revised",
        step_id="b",
        status="active",
        text="B revised",
        note="step note",
    )
    statuses = {step["id"]: step["status"] for step in updated["plan"]["steps"]}
    assert statuses == {"a": "pending", "b": "active"}
    assert updated["plan"]["objective"] == "Revised"
    assert updated["plan"]["steps"][1]["text"] == "B revised"
    assert updated["plan"]["steps"][1]["note"] == "step note"
    manager.manage_plan("mcp:plan", action="update", note="plan note")
    manager.manage_plan(
        "mcp:plan",
        action="update",
        steps=[
            {"id": "done", "text": "Done", "status": "completed"},
            {"id": "skip", "text": "Skip", "status": "skipped"},
        ],
    )

    with pytest.raises(ValueError, match="note is required"):
        manager.manage_plan("mcp:plan", action="block", note=" ")
    blocked = manager.manage_plan("mcp:plan", action="block", note="human input")
    assert blocked["plan"]["status"] == "blocked"
    with pytest.raises(ValueError, match="Cannot block"):
        manager.manage_plan("mcp:plan", action="block", note="again")
    resumed = manager.manage_plan("mcp:plan", action="resume")
    assert resumed["plan"]["status"] == "active"
    with pytest.raises(ValueError, match="Only a blocked"):
        manager.manage_plan("mcp:plan", action="resume")

    finished = manager.manage_plan("mcp:plan", action="finish")
    assert finished["plan"]["status"] == "completed"
    with pytest.raises(ValueError, match="Cannot finish"):
        manager.manage_plan("mcp:plan", action="finish")
    with pytest.raises(ValueError, match="already completed"):
        manager.manage_plan("mcp:plan", action="cancel")
    with pytest.raises(ValueError, match="Cannot update"):
        manager.manage_plan("mcp:plan", action="update", note="late")
    with pytest.raises(ValueError, match="action must be one of"):
        manager.manage_plan("mcp:plan", action="unknown")

    terminal = manager.manage(
        "mcp:plan", "user", action="finish", session_id=session_id
    )
    assert terminal["status"] == "completed"
    with pytest.raises(ValueError, match="Cannot resume a completed session"):
        manager.manage(
            "mcp:new", "user", action="resume", session_id=session_id, takeover=True
        )


def test_plan_cancel_and_continuation_pending_expiry(tmp_path, monkeypatch):
    manager = SessionRuntimeManager(tmp_path / ".state")
    now = [10_000.0]
    monkeypatch.setattr("local_shell_mcp.session_runtime.time.time", lambda: now[0])
    started = manager.manage("mcp:a", "user", action="start", objective="Goal")
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    manager.manage_plan(
        "mcp:a",
        action="start",
        objective="Goal",
        steps=[{"id": "work", "text": "Work"}],
    )
    now[0] += PLAN_EXECUTION_LEASE_S + 1
    assert manager.claim_plan_continuation(session_id) is not None
    now[0] += 5 * 60 + 1
    reclaimed = manager.claim_plan_continuation(session_id)
    assert reclaimed is not None
    manager.report_plan_continuation(session_id, accepted=True)
    with pytest.raises(ValueError, match="No plan continuation is pending"):
        manager.report_plan_continuation(session_id, accepted=True)

    cancelled = manager.manage(
        "mcp:a",
        "user",
        action="cancel",
        session_id=session_id,
        session_run_id=run_id,
    )
    assert cancelled["status"] == "cancelled"
    assert cancelled["plan"]["status"] == "cancelled"
    assert manager.current_session_id("mcp:a") is None
    assert manager.claim_plan_continuation(session_id) is None

    no_plan = manager.manage("mcp:b", "user", action="start", objective="No plan")
    with pytest.raises(ValueError, match="No plan exists"):
        manager.report_plan_continuation(no_plan["session_id"], accepted=False)


def test_human_resume_preserves_overdue_goal_lease(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Goal")
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    manager.manage_plan(
        "mcp:a",
        action="start",
        session_run_id=run_id,
        objective="Goal",
        steps=[{"id": "work", "text": "Work"}],
    )
    manager.manage_plan(
        "mcp:a", action="block", session_run_id=run_id, note="human input"
    )
    overdue = time.time() - PLAN_EXECUTION_LEASE_S - 1
    manager._sessions[session_id].plan.last_agent_activity = overdue

    resumed = manager.manage_plan_for_session(
        session_id,
        action="resume",
        actor="human",
        subject="user",
    )

    assert resumed["plan"]["last_agent_activity"] == overdue
    assert manager.claim_plan_continuation(session_id, subject="user") is not None
