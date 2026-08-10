from __future__ import annotations

import pytest

from local_shell_mcp.live_channel import LiveChannelManager
from local_shell_mcp.oauth import ALL_OAUTH_SCOPES
from local_shell_mcp.session_runtime import SessionRuntimeManager


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
    manager.manage(
        "mcp:first",
        "user",
        action="report",
        summary="Runtime is implemented",
        findings=["Live channels must not own plans"],
        next="Run integration tests",
        blockers=[],
    )
    manager.manage_plan(
        "mcp:first",
        action="start",
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
        manager.assert_current_run("mcp:agent-a")

    manager.assert_current_run("mcp:agent-b")
    reported = manager.manage(
        "mcp:agent-b",
        "user",
        action="report",
        session_id=session_id,
        summary="Agent B took over",
    )
    assert reported["progress"]["summary"] == "Agent B took over"


def test_session_access_is_scoped_to_principal(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    started = manager.manage("mcp:a", "alice", action="start", objective="Private task")

    with pytest.raises(PermissionError, match="different principal"):
        manager.manage(
            "mcp:b", "bob", action="get", session_id=started["session_id"]
        )


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
    second, _ = live.open(
        session_key="mcp:agent-b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=session_id,
    )

    assert second is first
    assert second.logical_session_id == session_id
    assert live.active_for_session("mcp:agent-b") is first


def test_session_finish_requires_terminal_plan(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    manager.manage("mcp:a", "user", action="start", objective="Task")
    manager.manage_plan(
        "mcp:a",
        action="start",
        objective="Task",
        steps=[{"id": "work", "text": "Work"}],
    )

    with pytest.raises(ValueError, match="plan is active or blocked"):
        manager.manage("mcp:a", "user", action="finish")

    manager.manage_plan("mcp:a", action="update", step_id="work", status="completed")
    manager.manage_plan("mcp:a", action="finish")
    finished = manager.manage("mcp:a", "user", action="finish")
    assert finished["status"] == "completed"
    assert finished["active_run"] is None
