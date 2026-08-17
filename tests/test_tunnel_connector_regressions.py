from __future__ import annotations

import pytest

import local_shell_mcp.tools as tools
from local_shell_mcp.models import CommandResult
from local_shell_mcp.session_runtime import SessionRuntimeManager
from local_shell_mcp.settings import get_settings


def _configure(tmp_path, monkeypatch, *, auth_mode: str = "none") -> None:
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_AUTH_MODE", auth_mode)
    monkeypatch.setenv("LOCAL_SHELL_MCP_REMOTE_ENABLED", "false")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_noauth_mode_advertises_noauth_security_scheme(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth_mode="none")

    advertised = await tools.build_mcp().list_tools()

    assert advertised
    for tool in advertised:
        schemes = (tool.meta or {}).get("securitySchemes", [])
        assert {scheme.get("type") for scheme in schemes} == {"noauth"}, tool.name


@pytest.mark.asyncio
async def test_run_python_uses_executable_quoting_for_powershell(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    monkeypatch.setenv("LOCAL_SHELL_MCP_SHELL_EXECUTABLE", "powershell.exe")
    monkeypatch.setenv(
        "LOCAL_SHELL_MCP_PYTHON_BIN", r"C:\Program Files\Python\python.exe"
    )
    get_settings.cache_clear()
    commands: list[str] = []

    async def fake_run_shell(command: str, **_kwargs) -> CommandResult:
        commands.append(command)
        return CommandResult(
            ok=True,
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            cwd=".",
            command=command,
            stdout="ok",
            stderr="",
            truncated=False,
        )

    monkeypatch.setattr(tools, "run_shell", fake_run_shell)

    result = await tools._run_python("print(1)")

    assert result["ok"] is True
    assert len(commands) == 1
    assert commands[0].startswith("& 'C:\\Program Files\\Python\\python.exe' '")


def test_multiplexed_stdio_routes_logical_sessions_by_durable_run_id(tmp_path):
    manager = SessionRuntimeManager(tmp_path / ".state")
    subject = "user"
    transport_key = "mcp-session:shared-tunnel"

    start_a_key = tools._logical_session_routing_key(
        transport_key,
        tool_name="session_manage",
        session_run_id=None,
        action="start",
    )
    start_b_key = tools._logical_session_routing_key(
        transport_key,
        tool_name="session_manage",
        session_run_id=None,
        action="start",
    )
    assert start_a_key != start_b_key

    session_a = manager.manage(start_a_key, subject, action="start", objective="A")
    session_b = manager.manage(start_b_key, subject, action="start", objective="B")
    session_a_id = session_a["session_id"]
    session_b_id = session_b["session_id"]
    run_a = session_a["active_run"]["run_id"]
    run_b = session_b["active_run"]["run_id"]

    route_a = tools._logical_session_routing_key(
        transport_key,
        tool_name="session_manage",
        session_run_id=run_a,
        action="report",
    )
    route_b = tools._logical_session_routing_key(
        transport_key,
        tool_name="session_manage",
        session_run_id=run_b,
        action="report",
    )
    assert route_a != route_b

    manager.manage(
        route_a,
        subject,
        action="report",
        session_run_id=run_a,
        summary="A-report",
    )
    manager.manage(
        route_b,
        subject,
        action="report",
        session_run_id=run_b,
        summary="B-report",
    )

    lease_a = manager.begin_tool_call(
        route_a,
        "call-a",
        expected_run_id=run_a,
        subject=subject,
        data={"tool": "run_shell"},
    )
    lease_b = manager.begin_tool_call(
        route_b,
        "call-b",
        expected_run_id=run_b,
        subject=subject,
        data={"tool": "run_shell"},
    )
    assert lease_a is not None
    assert lease_b is not None
    manager.finish_tool_call(lease_a, "tool.completed")
    manager.finish_tool_call(lease_b, "tool.completed")

    plan_a_key = tools._logical_session_routing_key(
        transport_key,
        tool_name="plan_manage",
        session_run_id=run_a,
        action="start",
    )
    plan_b_key = tools._logical_session_routing_key(
        transport_key,
        tool_name="plan_manage",
        session_run_id=run_b,
        action="start",
    )
    manager.manage_plan(
        plan_a_key,
        action="start",
        session_run_id=run_a,
        objective="Goal A",
        steps=[{"id": "a1", "text": "A"}],
    )
    manager.manage_plan(
        plan_b_key,
        action="start",
        session_run_id=run_b,
        objective="Goal B",
        steps=[{"id": "b1", "text": "B"}],
    )

    state_a = manager.get(session_a_id, subject=subject)
    state_b = manager.get(session_b_id, subject=subject)
    assert state_a["active_run"]["run_id"] == run_a
    assert state_b["active_run"]["run_id"] == run_b
    assert state_a["progress"]["summary"] == "A-report"
    assert state_b["progress"]["summary"] == "B-report"
    assert state_a["plan"]["objective"] == "Goal A"
    assert state_b["plan"]["objective"] == "Goal B"

    # Header-backed transports already have real client affinity and must retain
    # the existing one-session-per-transport routing semantics.
    assert (
        tools._logical_session_routing_key(
            "mcp-http:real-client",
            tool_name="session_manage",
            session_run_id=None,
            action="start",
        )
        == "mcp-http:real-client"
    )


def test_multiplexed_resume_routes_by_target_session_id():
    base = "mcp-session:shared-tunnel"
    first = tools._logical_session_routing_key(
        base,
        tool_name="session_manage",
        session_run_id=None,
        action="resume",
        session_id="s_first",
    )
    first_again = tools._logical_session_routing_key(
        base,
        tool_name="session_manage",
        session_run_id=None,
        action="resume",
        session_id="s_first",
    )
    second = tools._logical_session_routing_key(
        base,
        tool_name="session_manage",
        session_run_id=None,
        action="resume",
        session_id="s_second",
    )
    assert first == first_again == f"{base}:session:s_first"
    assert second == f"{base}:session:s_second"
    assert first != second
