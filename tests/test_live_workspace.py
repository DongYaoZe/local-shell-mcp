from __future__ import annotations

import asyncio
import hashlib
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.types import CallToolResult
from starlette.requests import Request

import local_shell_mcp.live_channel as live_channel_module
import local_shell_mcp.live_channel_routes as live_routes
import local_shell_mcp.session_runtime as session_runtime_module
from local_shell_mcp.auth import Principal
from local_shell_mcp.live_channel import (
    LIVE_EVENT_LIMIT,
    LIVE_RESOURCE_MIME,
    LIVE_RESOURCE_TEMPLATE_URI,
    LIVE_RESOURCE_URI,
    LIVE_RESOURCE_VERSIONED_URI,
    LiveChannelManager,
)
from local_shell_mcp.main import _build_mcp_http_app
from local_shell_mcp.oauth import ALL_OAUTH_SCOPES
from local_shell_mcp.session_runtime import SessionRuntimeManager
from local_shell_mcp.settings import get_settings
from local_shell_mcp.tools import build_mcp


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, auth: str = "oauth") -> None:
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_AUTH_MODE", auth)
    monkeypatch.setenv("LOCAL_SHELL_MCP_REMOTE_ENABLED", "false")
    monkeypatch.setenv("LOCAL_SHELL_MCP_PUBLIC_BASE_URL", "https://lsm.example.test")
    get_settings.cache_clear()
    monkeypatch.setattr(live_channel_module, "_MANAGER", LiveChannelManager())
    monkeypatch.setattr(
        session_runtime_module, "_MANAGER", SessionRuntimeManager(tmp_path / ".state")
    )


def test_live_workspace_resource_uri_stays_stable_with_versioned_alias():
    asset = Path(live_channel_module.__file__).resolve().parent / "ui_static" / "live-workspace.html"
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:16]
    assert LIVE_RESOURCE_URI == "ui://local-shell-mcp/live-workspace.html"
    assert f"ui://local-shell-mcp/live-workspace-{digest}.html" == LIVE_RESOURCE_VERSIONED_URI


def test_live_workspace_tokens_rotate_and_events_are_bounded():
    manager = LiveChannelManager()
    parent_deadline = time.time() + 60
    channel, first_token = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        parent_expires_at=parent_deadline,
    )
    same_channel, second_token = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        parent_expires_at=parent_deadline,
    )

    assert same_channel.live_id == channel.live_id
    assert first_token != second_token
    assert manager.authenticate(first_token) is None
    assert manager.authenticate(second_token) is channel
    assert channel.expires_at <= parent_deadline

    for index in range(LIVE_EVENT_LIMIT + 50):
        manager.publish_channel(
            channel.live_id,
            "test.event",
            actor="system",
            data={"index": index},
        )

    assert len(channel.events) == LIVE_EVENT_LIMIT
    assert channel.events[-1]["data"]["index"] == LIVE_EVENT_LIMIT + 49
    assert channel.events[0]["seq"] == channel.seq - LIVE_EVENT_LIMIT + 1


def test_live_workspace_can_reattach_a_second_mcp_session_by_live_id():
    manager = LiveChannelManager()
    channel, first_token = manager.open(
        session_key="mcp:model-session",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    attached, app_token = manager.open(
        session_key="mcp:app-session",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=channel.live_id,
    )

    assert attached is channel
    assert manager.active_for_session("mcp:model-session") is channel
    assert manager.active_for_session("mcp:app-session") is channel
    assert app_token == first_token
    assert manager.authenticate(first_token) is channel
    assert manager.authenticate(app_token) is channel

    manager.publish_for_session(
        "mcp:model-session",
        "tool.completed",
        data={"tool": "run_shell_tool", "call_id": "model-call"},
    )
    assert channel.events[-1]["data"]["call_id"] == "model-call"

    with pytest.raises(PermissionError, match="different principal"):
        manager.open(
            session_key="mcp:other-user",
            subject="other",
            scopes=tuple(ALL_OAUTH_SCOPES),
            live_id=channel.live_id,
        )


def test_live_workspace_recovery_is_one_shot_and_does_not_merge_same_subject_sessions():
    manager = LiveChannelManager()
    first, _ = manager.open(
        session_key="mcp:chat-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    second, _ = manager.open(
        session_key="mcp:chat-b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    assert second is not first

    recovered, token = manager.open(
        session_key="mcp:recovered-app-1",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-live-id-after-restart",
    )
    cached_view, cached_token = manager.open(
        session_key="mcp:recovered-app-2",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-live-id-after-restart",
    )
    assert cached_view is recovered
    assert cached_token == token

    assert manager.claim_recovery_session("mcp:model-after-restart", "user") is recovered
    assert manager.active_for_session("mcp:model-after-restart") is recovered
    assert manager.claim_recovery_session("mcp:unrelated-chat", "user") is None
    assert manager.active_for_session("mcp:unrelated-chat") is None


def test_live_workspace_recovery_refuses_ambiguous_same_subject_workspaces():
    manager = LiveChannelManager()
    first, _ = manager.open(
        session_key="mcp:recovered-app-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-chat-a",
    )
    second, _ = manager.open(
        session_key="mcp:recovered-app-b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-chat-b",
    )
    assert first is not second

    assert manager.claim_recovery_session("mcp:model-unknown-chat", "user") is None
    assert manager.active_for_session("mcp:model-unknown-chat") is None

    first.expires_at = 0
    assert manager.claim_recovery_session("mcp:model-chat-b", "user") is second
    assert manager.active_for_session("mcp:model-chat-b") is second


@pytest.mark.asyncio
async def test_live_workspace_expiry_publish_and_wait_paths():
    manager = LiveChannelManager()
    channel, token = manager.open(
        session_key="mcp:events",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    assert manager.authenticate(None) is None
    assert manager.publish_channel("missing", "ignored", actor="system") is None

    immediate = await manager.wait_events(channel, 0, timeout_s=0.1)
    assert immediate and immediate[0]["type"] == "channel.opened"

    after = channel.seq
    assert await manager.wait_events(channel, after, timeout_s=0.01) == []

    async def publish_later() -> None:
        await asyncio.sleep(0.01)
        manager.publish_channel(
            channel.live_id,
            "job.progress",
            actor="system",
            data={"progress": 50},
        )

    publisher = asyncio.create_task(publish_later())
    waited = await manager.wait_events(channel, after, timeout_s=0.5)
    await publisher
    assert waited[-1]["type"] == "job.progress"

    channel.expires_at = 0
    assert manager.authenticate(token) is None
    assert manager.active_for_session("mcp:events") is None
    assert manager.by_id(channel.live_id) is None


def test_plan_state_machine_and_auto_promotion(tmp_path):
    sessions = SessionRuntimeManager(tmp_path / ".state")
    started_session = sessions.manage(
        "mcp:plan", "user", action="start", objective="Make the change fully ready"
    )
    session_id = started_session["session_id"]

    started = sessions.manage_plan(
        "mcp:plan",
        action="start",
        objective="Make the change fully ready",
        steps=[{"id": "inspect", "text": "Inspect"}, {"id": "test", "text": "Test"}],
    )
    assert started["session_id"] == session_id
    assert started["goal_mode"] is True
    assert [step["status"] for step in started["plan"]["steps"]] == ["active", "pending"]

    updated = sessions.manage_plan(
        "mcp:plan",
        action="update",
        step_id="inspect",
        status="completed",
    )
    assert [step["status"] for step in updated["plan"]["steps"]] == ["completed", "active"]

    with pytest.raises(ValueError, match="unfinished steps"):
        sessions.manage_plan("mcp:plan", action="finish")

    sessions.manage_plan("mcp:plan", action="update", step_id="test", status="completed")
    finished = sessions.manage_plan("mcp:plan", action="finish", note="done")
    assert finished["goal_mode"] is False
    assert finished["plan"]["status"] == "completed"
    assert sessions.plan_state(session_id)["status"] == "completed"


def test_plan_requires_logical_session_and_block_stops_continuation(tmp_path, monkeypatch):
    sessions = SessionRuntimeManager(tmp_path / ".state")
    with pytest.raises(RuntimeError, match="logical session"):
        sessions.manage_plan(
            "mcp:missing",
            action="start",
            objective="Long task",
            steps=[{"text": "Do work"}],
        )

    now = [1_000.0]
    monkeypatch.setattr(session_runtime_module.time, "time", lambda: now[0])
    started_session = sessions.manage(
        "mcp:block", "user", action="start", objective="Long task"
    )
    session_id = started_session["session_id"]
    sessions.manage_plan(
        "mcp:block",
        action="start",
        objective="Long task",
        steps=[{"text": "Do work"}],
    )
    now[0] += session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    assert sessions.claim_plan_continuation(session_id) is not None
    sessions.report_plan_continuation(session_id, accepted=True)

    sessions.manage_plan("mcp:block", action="block", note="Need user input")
    now[0] += session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    assert sessions.claim_plan_continuation(session_id) is None

    resumed = sessions.manage_plan("mcp:block", action="resume")
    assert resumed["plan"]["status"] == "active"
    assert resumed["plan"]["continuation_due"] is False


def test_plan_continuation_lease_rejection_and_hard_cap(tmp_path, monkeypatch):
    sessions = SessionRuntimeManager(tmp_path / ".state")
    now = [1_000.0]
    monkeypatch.setattr(session_runtime_module.time, "time", lambda: now[0])
    started_session = sessions.manage(
        "mcp:continue", "user", action="start", objective="Keep going until done"
    )
    session_id = started_session["session_id"]
    sessions.manage_plan(
        "mcp:continue",
        action="start",
        objective="Keep going until done",
        steps=[{"id": "work", "text": "Work"}],
    )

    now[0] += session_runtime_module.PLAN_EXECUTION_LEASE_S - 1
    assert sessions.claim_plan_continuation(session_id) is None

    now[0] += 2
    rejected = sessions.claim_plan_continuation(session_id)
    assert rejected is not None
    assert rejected["continuation_count"] == 1
    sessions.report_plan_continuation(session_id, accepted=False, error="host busy")
    assert sessions.plan_state(session_id)["continuation_count"] == 0

    for expected in range(1, session_runtime_module.PLAN_MAX_CONTINUATIONS + 1):
        now[0] += session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
        claim = sessions.claim_plan_continuation(session_id)
        assert claim is not None
        assert claim["continuation_count"] == expected
        assert sessions.claim_plan_continuation(session_id) is None
        sessions.report_plan_continuation(session_id, accepted=True)

    now[0] += session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    assert sessions.claim_plan_continuation(session_id) is None
    assert sessions.plan_state(session_id)["auto_continue_exhausted"] is True


def test_mcp_session_key_uses_request_session_identity():
    class Session:
        pass

    class FakeMcp:
        def __init__(self, session, headers=None):
            self.session = session
            self.headers = headers or {}

        def get_context(self):
            return type(
                "Context",
                (),
                {
                    "request_context": type(
                        "RequestContext",
                        (),
                        {
                            "session": self.session,
                            "request": type("Request", (), {"headers": self.headers})(),
                        },
                    )()
                },
            )()

    assert live_channel_module.mcp_session_key(FakeMcp(Session(), {"mcp-session-id": "abc123"})) == (
        "mcp-http:abc123"
    )
    first_session = Session()
    second_session = Session()
    first_key = live_channel_module.mcp_session_key(FakeMcp(first_session))
    assert live_channel_module.mcp_session_key(FakeMcp(first_session)) == first_key
    assert live_channel_module.mcp_session_key(FakeMcp(second_session)) != first_key


@pytest.mark.asyncio
async def test_mcp_app_resource_and_render_result_hide_live_token(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()

    tools = {tool.name: tool for tool in await mcp.list_tools()}
    render_tool = tools["open_live_workspace"]
    reconnect_tool = tools["live_workspace_reconnect"]
    assert render_tool.meta["ui"]["resourceUri"] == LIVE_RESOURCE_VERSIONED_URI
    assert render_tool.meta["ui/resourceUri"] == LIVE_RESOURCE_VERSIONED_URI
    assert render_tool.meta["openai/outputTemplate"] == LIVE_RESOURCE_VERSIONED_URI
    assert render_tool.meta["openai/widgetAccessible"] is True
    assert "live_id" not in render_tool.inputSchema["properties"]
    assert render_tool.meta["securitySchemes"][0]["scopes"] == list(ALL_OAUTH_SCOPES)
    assert render_tool.outputSchema["title"] == "LiveChannelResult"
    assert render_tool.annotations.readOnlyHint is True
    assert render_tool.annotations.destructiveHint is False
    assert render_tool.annotations.idempotentHint is True
    assert reconnect_tool.meta["ui"] == {"visibility": ["app"]}
    assert "ui/resourceUri" not in reconnect_tool.meta
    assert "openai/outputTemplate" not in reconnect_tool.meta

    resources = {str(resource.uri): resource for resource in await mcp.list_resources()}
    resource = resources[LIVE_RESOURCE_URI]
    assert LIVE_RESOURCE_VERSIONED_URI in resources
    assert resource.mimeType == LIVE_RESOURCE_MIME
    assert resource.meta["ui"]["domain"] == "https://lsm.example.test"
    assert resource.meta["ui"]["csp"]["connectDomains"] == [
        "https://lsm.example.test",
        "wss://lsm.example.test",
    ]
    assert resource.meta["ui"]["permissions"] == {"clipboardWrite": {}}
    assert resource.meta["openai/widgetDomain"] == "https://lsm.example.test"

    result = await mcp.call_tool("open_live_workspace", {"machine": "local", "cwd": "."})
    assert isinstance(result, CallToolResult)
    assert result.structuredContent["live_id"]
    assert "token" not in result.structuredContent
    hidden = result.meta["local-shell-mcp/live"]
    assert hidden["token"]
    assert hidden["apiBase"] == "https://lsm.example.test"
    assert hidden["token"] not in (tmp_path / "audit.jsonl").read_text(encoding="utf-8")

    reconnected = await mcp.call_tool(
        "live_workspace_reconnect",
        {"machine": "local", "cwd": ".", "live_id": result.structuredContent["live_id"]},
    )
    assert isinstance(reconnected, CallToolResult)
    assert reconnected.structuredContent["live_id"] == result.structuredContent["live_id"]
    reconnect_token = reconnected.meta["local-shell-mcp/live"]["token"]
    assert reconnect_token == hidden["token"]
    assert reconnect_token not in (tmp_path / "audit.jsonl").read_text(encoding="utf-8")

    templates = {
        str(template.uriTemplate): template for template in await mcp.list_resource_templates()
    }
    assert LIVE_RESOURCE_TEMPLATE_URI in templates

    for uri in (
        LIVE_RESOURCE_URI,
        LIVE_RESOURCE_VERSIONED_URI,
        "ui://local-shell-mcp/live-workspace-previous-cache-key.html",
    ):
        contents = list(await mcp.read_resource(uri))
        assert contents[0].mime_type == LIVE_RESOURCE_MIME
        assert "local-shell-mcp-live-workspace" in str(contents[0].content)


@pytest.mark.asyncio
async def test_live_workspace_keeps_model_and_human_mutations_collaborative(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    result = await mcp.call_tool("open_live_workspace", {"cwd": "."})
    assert isinstance(result, CallToolResult)
    live_token = result.meta["local-shell-mcp/live"]["token"]
    channel = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert channel is not None

    reopened = await mcp.call_tool("open_live_workspace", {"cwd": "."})
    assert isinstance(reopened, CallToolResult)
    refreshed_live_token = reopened.meta["local-shell-mcp/live"]["token"]
    assert refreshed_live_token != live_token
    await mcp.call_tool("write_file", {"path": "shared.txt", "content": "shared"})
    assert (tmp_path / "shared.txt").read_text(encoding="utf-8") == "shared"
    _, structured = await mcp.call_tool("list_files", {"path": "."})
    assert structured["ok"] is True
    assert live_channel_module.get_live_channel_manager().authenticate(live_token) is None
    assert live_channel_module.get_live_channel_manager().authenticate(refreshed_live_token) is channel
    event_types = [event["type"] for event in channel.events]
    assert "tool.completed" in event_types


def test_live_http_token_cors_and_collaborative_human_mutation(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    manager = live_channel_module.get_live_channel_manager()
    session_manager = session_runtime_module.get_session_runtime_manager()
    logical = session_manager.manage(
        "mcp:http-test", "user", action="start", objective="Exercise human goal controls"
    )
    channel, token = manager.open(
        session_key="mcp:http-test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=logical["session_id"],
    )
    headers = {"Authorization": f"Bearer {token}", "Origin": "https://chatgpt.com"}
    app = _build_mcp_http_app(build_mcp())

    with TestClient(app, base_url="http://testserver") as client:
        preflight = client.options(
            "/api/live/snapshot",
            headers={
                "Origin": "https://chatgpt.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert preflight.status_code == 204
        assert preflight.headers["access-control-allow-origin"] == "*"

        snapshot = client.get("/api/live/snapshot", headers=headers)
        assert snapshot.status_code == 200
        assert snapshot.headers["access-control-allow-origin"] == "*"
        assert snapshot.json()["data"]["channel"]["live_id"] == channel.live_id

        bootstrap = client.get("/api/ui/bootstrap", headers=headers)
        assert bootstrap.status_code == 200

        events = client.get("/api/live/events?after=0&timeout=1", headers=headers)
        assert events.status_code == 200
        assert events.json()["data"]["events"]

        invalid_cursor = client.get("/api/live/events?after=not-a-number", headers=headers)
        assert invalid_cursor.status_code == 400
        assert invalid_cursor.json()["message"] == "Invalid event cursor"

        session_manager.manage_plan(
            "mcp:http-test",
            action="start",
            objective="Exercise human goal controls",
            steps=[{"id": "work", "text": "Do the work"}],
        )
        paused = client.post("/api/live/plan", headers=headers, json={"action": "pause"})
        assert paused.status_code == 200
        assert paused.json()["data"]["plan"]["status"] == "blocked"
        resumed = client.post("/api/live/plan", headers=headers, json={"action": "resume"})
        assert resumed.status_code == 200
        assert resumed.json()["data"]["plan"]["status"] == "active"
        cancelled = client.post("/api/live/plan", headers=headers, json={"action": "cancel"})
        assert cancelled.status_code == 200
        assert cancelled.json()["data"]["plan"]["status"] == "cancelled"
        assert any(
            event["type"] == "plan.cancelled" and event["actor"] == "human"
            for event in channel.events
        )

        written = client.post(
            "/api/ui/files/write",
            headers=headers,
            json={"machine": "local", "path": "human.txt", "content": "shared"},
        )
        assert written.status_code == 200
        assert (tmp_path / "human.txt").read_text(encoding="utf-8") == "shared"

        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        (tmp_path / "tracked.txt").write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Live Workspace Test",
                "-c",
                "user.email=live-workspace@example.invalid",
                "commit",
                "-qm",
                "seed",
            ],
            cwd=tmp_path,
            check=True,
        )
        (tmp_path / "tracked.txt").write_text("after\n", encoding="utf-8")
        git = client.get("/api/live/git?cwd=.", headers=headers)
        assert git.status_code == 200
        git_data = git.json()["data"]
        assert "tracked.txt" in git_data["status"]["stdout"]
        assert "before" in git_data["diff"]["stdout"]
        assert any(
            event["type"] == "human.inspected_diff" for event in channel.events
        )

        subprocess.run(["git", "checkout", "--", "tracked.txt"], cwd=tmp_path, check=True)
        clean_git = client.get("/api/live/git?cwd=.", headers=headers)
        assert clean_git.status_code == 200
        assert clean_git.json()["data"]["diff"]["stdout"] == ""

        # A live token is deliberately not valid for the MCP transport itself.
        mcp_attempt = client.post(
            "/mcp",
            headers={**headers, "Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        assert mcp_attempt.status_code in {401, 403}


def test_live_http_token_authenticates_when_global_auth_is_disabled(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = live_channel_module.get_live_channel_manager()
    channel, token = manager.open(
        session_key="mcp:no-auth-http",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        same_origin = client.get(
            "/api/ui/files?machine=local&path=.",
            headers={"Origin": "http://testserver"},
        )
        anonymous_cross_origin = client.get(
            "/api/ui/files?machine=local&path=.",
            headers={"Origin": "https://malicious.example"},
        )
        snapshot = client.get(
            "/api/live/snapshot",
            headers={"Authorization": f"Bearer {token}", "Origin": "https://chatgpt.com"},
        )
        _, replacement = manager.open(
            session_key="mcp:no-auth-http",
            subject="user",
            scopes=tuple(ALL_OAUTH_SCOPES),
        )
        stale_ui = client.get(
            "/api/ui/files?machine=local&path=.",
            headers={"Authorization": f"Bearer {token}", "Origin": "https://chatgpt.com"},
        )
        current_ui = client.get(
            "/api/ui/files?machine=local&path=.",
            headers={"Authorization": f"Bearer {replacement}", "Origin": "https://chatgpt.com"},
        )
    assert same_origin.status_code == 200
    assert anonymous_cross_origin.status_code == 401
    assert snapshot.status_code == 200
    assert snapshot.json()["data"]["channel"]["live_id"] == channel.live_id
    assert stale_ui.status_code == 401
    assert current_ui.status_code == 200


def test_live_events_empty_batch_does_not_advance_cursor(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = live_channel_module.get_live_channel_manager()
    _, token = manager.open(
        session_key="mcp:cursor-race",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    async def empty_wait(channel, after, timeout_s):  # noqa: ARG001
        manager.publish_channel(
            channel.live_id,
            "tool.completed",
            actor="agent",
            data={"tool": "late"},
        )
        return []

    monkeypatch.setattr(manager, "wait_events", empty_wait)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.get(
            "/api/live/events?after=0&timeout=1",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["events"] == []
    assert data["cursor"] == 0
    assert manager.events_since(manager.authenticate(token), 0)[-1]["data"]["tool"] == "late"


def test_live_workspace_is_hidden_when_ui_is_disabled(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    monkeypatch.setenv("LOCAL_SHELL_MCP_UI_ENABLED", "false")
    get_settings.cache_clear()
    mcp = build_mcp()

    async def inspect_surface():
        tools = {tool.name for tool in await mcp.list_tools()}
        resources = {str(resource.uri) for resource in await mcp.list_resources()}
        return tools, resources

    tools, resources = asyncio.run(inspect_surface())
    assert "open_live_workspace" not in tools
    assert LIVE_RESOURCE_URI not in resources

    app = _build_mcp_http_app(mcp)
    with TestClient(app, base_url="http://testserver") as client:
        assert client.get("/api/live/snapshot").status_code == 404


def test_live_workspace_is_hidden_in_stdio_mode(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    monkeypatch.setenv("LOCAL_SHELL_MCP_MODE", "stdio")
    get_settings.cache_clear()
    mcp = build_mcp()

    async def inspect_surface():
        tools = {tool.name for tool in await mcp.list_tools()}
        resources = {str(resource.uri) for resource in await mcp.list_resources()}
        return tools, resources

    tools, resources = asyncio.run(inspect_surface())
    assert "open_live_workspace" not in tools
    assert LIVE_RESOURCE_URI not in resources


def test_live_git_routes_remote_inspection_to_selected_machine(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    manager = live_channel_module.get_live_channel_manager()
    _, token = manager.open(
        session_key="mcp:remote-git",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    class FakeRemote:
        def __init__(self):
            self.calls = []

        async def call(self, machine, tool, args, timeout_s=None):
            self.calls.append((machine, tool, args, timeout_s))
            command = args["command"]
            stdout = "## main\n" if "status" in command else "diff --git a/remote.txt b/remote.txt\n"
            return {
                "ok": True,
                "message": "",
                "data": {
                    "ok": True,
                    "exit_code": 0,
                    "timed_out": False,
                    "duration_ms": 1,
                    "cwd": ".",
                    "command": command,
                    "stdout": stdout,
                    "stderr": "",
                    "truncated": False,
                },
            }

    fake_remote = FakeRemote()
    monkeypatch.setattr(live_routes, "remote_manager", lambda: fake_remote)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.get(
            "/api/live/git?machine=worker&cwd=.",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["machine"] == "worker"
    assert "remote.txt" in data["diff"]["stdout"]
    assert len(fake_remote.calls) == 3
    assert all(call[0] == "worker" and call[1] == "run_shell_tool" for call in fake_remote.calls)
    assert all(call[2]["_human"] is True for call in fake_remote.calls)


def test_live_route_helpers_reject_missing_or_expired_workspace(monkeypatch):
    request = Request({"type": "http", "method": "GET", "path": "/api/live/snapshot", "headers": []})
    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": "shell:read"},
    )
    with pytest.raises(Exception, match="live-workspace token"):
        live_routes._live_channel(request)

    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": "shell:read", "live_id": "expired"},
    )
    monkeypatch.setattr(live_routes, "get_live_channel_manager", lambda: LiveChannelManager())
    with pytest.raises(Exception, match="Live workspace expired"):
        live_routes._live_channel(request)


def test_live_route_principal_falls_back_to_request_verification(monkeypatch):
    request = Request({"type": "http", "method": "GET", "path": "/api/live/snapshot", "headers": []})
    expected = Principal(email=None, subject="verified", claims={})
    monkeypatch.setattr(live_routes, "current_principal", lambda: None)
    monkeypatch.setattr(live_routes, "verify_request", lambda _request: expected)
    assert live_routes._principal(request) is expected


def test_live_route_generic_error_response():
    response = live_routes._error(RuntimeError("boom"))
    assert response.status_code == 400
    assert b"boom" in response.body


@pytest.mark.asyncio
async def test_live_remote_git_shell_rejects_failed_and_invalid_payloads(monkeypatch):
    class FakeRemote:
        def __init__(self):
            self.response = {"ok": False, "message": "remote failed"}

        async def call(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return self.response

    fake = FakeRemote()
    monkeypatch.setattr(live_routes, "remote_manager", lambda: fake)

    with pytest.raises(RuntimeError, match="remote failed"):
        await live_routes._run_machine_shell(
            "worker",
            "git status --short --branch",
            cwd=".",
            timeout_s=15,
            max_output_bytes=80_000,
        )

    fake.response = {"ok": True, "data": "not-a-dict"}
    with pytest.raises(RuntimeError, match="invalid data"):
        await live_routes._run_machine_shell(
            "worker",
            "git status --short --branch",
            cwd=".",
            timeout_s=15,
            max_output_bytes=80_000,
        )


@pytest.mark.asyncio
async def test_live_snapshot_returns_missing_token_error():
    request = Request({"type": "http", "method": "GET", "path": "/api/live/snapshot", "headers": []})
    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": "shell:read"},
    )
    response = await live_routes.live_snapshot(request)
    assert response.status_code == 403
    assert b"live-workspace token" in response.body
