from __future__ import annotations

import copy
import time

import pytest

from local_shell_mcp.auth import Principal
from local_shell_mcp.session_runtime import (
    PLAN_EXECUTION_LEASE_S,
    SESSION_RUN_HISTORY_LIMIT,
    AgentRun,
    SessionRuntimeManager,
)


def test_resume_persistence_failure_restores_both_sessions(tmp_path, monkeypatch):
    state_dir = tmp_path / ".state"
    manager = SessionRuntimeManager(state_dir)
    first = manager.manage("mcp:a", "user", action="start", objective="First")
    target = manager.manage("mcp:b", "user", action="start", objective="Target")
    first_id = first["session_id"]
    first_run = first["active_run"]["run_id"]
    target_id = target["session_id"]
    target_run = target["active_run"]["run_id"]
    original_save = manager._save_locked
    failed = False

    def fail_resume_activity(session):
        nonlocal failed
        if (
            not failed
            and session.session_id == target_id
            and session.activity
            and session.activity[-1]["type"] == "session.resumed"
        ):
            failed = True
            raise OSError("forced resume persistence failure")
        return original_save(session)

    monkeypatch.setattr(manager, "_save_locked", fail_resume_activity)
    with pytest.raises(OSError, match="forced resume persistence failure"):
        manager.manage(
            "mcp:a",
            "user",
            action="resume",
            session_id=target_id,
            takeover=True,
        )

    assert manager.current_session_id("mcp:a", subject="user") == first_id
    assert manager.get(first_id, subject="user")["active_run"]["run_id"] == first_run
    assert manager.get(target_id, subject="user")["active_run"]["run_id"] == target_run

    restored = SessionRuntimeManager(state_dir)
    assert restored.get(first_id, subject="user")["active_run"]["run_id"] == first_run
    assert restored.get(target_id, subject="user")["active_run"]["run_id"] == target_run


def test_agent_session_resume_refreshes_goal_lease(tmp_path):
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
    logical = manager._sessions[session_id]
    assert logical.plan is not None
    logical.plan.last_agent_activity = time.time() - PLAN_EXECUTION_LEASE_S - 1

    before_resume = time.time()
    resumed = manager.manage(
        "mcp:a",
        "user",
        action="resume",
        session_id=session_id,
        takeover=True,
    )

    assert resumed["plan"]["last_agent_activity"] >= before_resume
    assert manager.claim_plan_continuation(session_id, subject="user") is None


def test_existing_attachment_is_rejected_after_principal_change(tmp_path, monkeypatch):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user-a", action="start", objective="Task")
    run_id = started["active_run"]["run_id"]

    with pytest.raises(PermissionError, match="different principal"):
        manager.begin_tool_call(
            "mcp:a",
            "call-1",
            expected_run_id=run_id,
            subject="user-b",
        )
    assert manager.current_session_id("mcp:a") is None

    manager.manage(
        "mcp:a",
        "user-a",
        action="resume",
        session_id=started["session_id"],
        takeover=True,
    )
    monkeypatch.setattr(
        "local_shell_mcp.session_runtime.current_principal",
        lambda: Principal(email=None, subject="user-b", claims={}),
    )
    with pytest.raises(PermissionError, match="different principal"):
        manager.manage_plan("mcp:a", action="get")
    assert manager.current_session_id("mcp:a") is None



def test_cross_principal_transport_reuse_does_not_detach_previous_run(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    first = manager.manage("shared", "alice", action="start", objective="Alice task")
    first_id = first["session_id"]
    first_run_id = first["active_run"]["run_id"]

    second = manager.manage("shared", "bob", action="start", objective="Bob task")

    alice = manager.get(first_id, subject="alice")
    assert alice["active_run"]["run_id"] == first_run_id
    assert alice["active_run"]["status"] == "active"
    assert manager.current_session_id("shared", subject="bob") == second["session_id"]


def test_current_session_id_drops_attachment_for_missing_session(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    session_id = started["session_id"]
    manager._sessions.pop(session_id)

    assert manager.current_session_id("mcp:a", subject="user") is None
    assert "mcp:a" not in manager._attachments


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("progress", [1], "invalid progress state"),
        ("runs", {"bad": 1}, "invalid run state"),
        ("activity", {"bad": 1}, "invalid activity state"),
        ("in_flight_calls", [1], "invalid in-flight tool state"),
    ],
)
def test_session_payload_rejects_malformed_nested_state(tmp_path, field, value, message):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    payload = manager._session_to_payload(manager._sessions[started["session_id"]])
    payload[field] = value

    with pytest.raises(ValueError, match=message):
        manager._session_from_payload(payload)


def test_session_and_plan_payload_reject_invalid_top_level_shapes(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    with pytest.raises(ValueError, match="session metadata must be an object"):
        manager._session_from_payload([])
    with pytest.raises(ValueError, match="invalid plan state"):
        manager._plan_from_payload([])
    with pytest.raises(ValueError, match="invalid plan steps"):
        manager._plan_from_payload({"steps": {}})


def test_session_loader_skips_corrupt_state_files(tmp_path):
    state_dir = tmp_path / ".state"
    seeded = SessionRuntimeManager(state_dir)
    started = seeded.manage("mcp:a", "user", action="start", objective="Valid")
    sessions_dir = state_dir / "sessions"
    (sessions_dir / "ignored.txt").write_text("not session state", encoding="utf-8")
    (sessions_dir / "broken-json.json").write_text("{", encoding="utf-8")
    (sessions_dir / "broken-utf8.json").write_bytes(b"\xff\xfe")

    restored = SessionRuntimeManager(state_dir)
    listed = restored.manage("mcp:list", "user", action="list")["sessions"]
    assert [item["session_id"] for item in listed] == [started["session_id"]]
    assert restored._load_session_from_store_locked("missing") is None
    assert restored._load_session_from_store_locked("broken-json") is None


def test_bounded_run_history_keeps_an_old_active_run():
    runs = [
        AgentRun(
            run_id=f"r_{index}",
            session_key="persisted",
            created_at=float(index),
            updated_at=float(index),
            status="active" if index == 0 else "superseded",
        )
        for index in range(SESSION_RUN_HISTORY_LIMIT + 1)
    ]

    bounded = SessionRuntimeManager._bounded_run_history(runs, runs[0].run_id)
    assert len(bounded) == SESSION_RUN_HISTORY_LIMIT
    assert bounded[0].run_id == runs[0].run_id
    assert bounded[-1].run_id == runs[-1].run_id


def test_snapshot_restore_reports_rollback_failure(tmp_path, monkeypatch):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "user", action="start", objective="Task")
    snapshot = copy.deepcopy(manager._sessions[started["session_id"]])
    error = RuntimeError("original failure")

    def fail_save(_session):
        raise OSError("rollback failed")

    monkeypatch.setattr(manager, "_save_locked", fail_save)
    manager._restore_snapshot_locked(snapshot, error, context="Test restore")

    assert error.__notes__ == ["Test restore rollback warning: OSError: rollback failed"]
    assert manager._in_flight_count_locked("missing") == 0
