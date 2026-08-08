from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.types import CallToolResult
from starlette.requests import Request

import local_shell_mcp.live_channel as live_channel_module
import local_shell_mcp.live_channel_routes as live_routes
from local_shell_mcp.auth import Principal
from local_shell_mcp.live_channel import (
    LIVE_EVENT_LIMIT,
    LIVE_RESOURCE_MIME,
    LIVE_RESOURCE_URI,
    HumanCollaborationRequiredError,
    HumanControlActiveError,
    LiveChannelManager,
)
from local_shell_mcp.main import _build_mcp_http_app
from local_shell_mcp.oauth import ALL_OAUTH_SCOPES
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
    assert manager.authenticate(first_token) is None
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


def test_live_workspace_auto_reattaches_only_when_subject_channel_is_unambiguous():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:app-after-restart",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    assert manager.attach_session_for_subject("mcp:model-after-restart", "user") is channel
    assert manager.active_for_session("mcp:model-after-restart") is channel
    assert manager.attach_session_for_subject("mcp:other", "other") is None

    manager.open(
        session_key="mcp:second-app",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    assert manager.attach_session_for_subject("mcp:ambiguous-model", "user") is None
    assert manager.active_for_session("mcp:ambiguous-model") is None


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


def test_live_workspace_rejects_invalid_control_and_missing_workspace():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:control-errors",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    with pytest.raises(ValueError, match="Unsupported control mode"):
        manager.set_control(channel, "invalid")
    with pytest.raises(HumanCollaborationRequiredError, match="no longer available"):
        manager.require_human_mutation_allowed("missing")


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


def test_control_modes_enforce_both_sides():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    with pytest.raises(HumanCollaborationRequiredError):
        manager.require_human_mutation_allowed(channel.live_id)

    manager.set_control(channel, "shared")
    manager.require_human_mutation_allowed(channel.live_id)
    manager.require_agent_mutation_allowed("mcp:test", "write_file")

    manager.set_control(channel, "human")
    manager.require_human_mutation_allowed(channel.live_id)
    with pytest.raises(HumanControlActiveError):
        manager.require_agent_mutation_allowed("mcp:test", "write_file")

    manager.set_control(channel, "agent")
    manager.require_agent_mutation_allowed("mcp:test", "write_file")


@pytest.mark.asyncio
async def test_mcp_app_resource_and_render_result_hide_live_token(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()

    tools = {tool.name: tool for tool in await mcp.list_tools()}
    render_tool = tools["open_live_workspace"]
    assert render_tool.meta["ui"]["resourceUri"] == LIVE_RESOURCE_URI
    assert render_tool.meta["ui/resourceUri"] == LIVE_RESOURCE_URI
    assert render_tool.meta["openai/outputTemplate"] == LIVE_RESOURCE_URI
    assert render_tool.meta["openai/widgetAccessible"] is True
    assert render_tool.meta["securitySchemes"][0]["scopes"] == list(ALL_OAUTH_SCOPES)
    assert render_tool.outputSchema["title"] == "LiveChannelResult"
    assert render_tool.annotations.readOnlyHint is True
    assert render_tool.annotations.destructiveHint is False
    assert render_tool.annotations.idempotentHint is True

    resources = {str(resource.uri): resource for resource in await mcp.list_resources()}
    resource = resources[LIVE_RESOURCE_URI]
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

    contents = list(await mcp.read_resource(LIVE_RESOURCE_URI))
    assert contents[0].mime_type == LIVE_RESOURCE_MIME
    assert "local-shell-mcp-live-workspace" in str(contents[0].content)


@pytest.mark.asyncio
async def test_human_takeover_blocks_model_mutation_but_not_reads(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    result = await mcp.call_tool("open_live_workspace", {"cwd": "."})
    assert isinstance(result, CallToolResult)
    live_token = result.meta["local-shell-mcp/live"]["token"]
    channel = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert channel is not None
    live_channel_module.get_live_channel_manager().set_control(channel, "human")

    reopened = await mcp.call_tool("open_live_workspace", {"cwd": "."})
    assert isinstance(reopened, CallToolResult)
    refreshed_live_token = reopened.meta["local-shell-mcp/live"]["token"]
    assert refreshed_live_token != live_token
    with pytest.raises(Exception, match="human takeover mode"):
        await mcp.call_tool("write_file", {"path": "blocked.txt", "content": "blocked"})
    with pytest.raises(Exception, match="human takeover mode"):
        await mcp.call_tool("browser_snapshot", {"session_id": "missing"})

    assert not (tmp_path / "blocked.txt").exists()
    _, structured = await mcp.call_tool("list_files", {"path": "."})
    assert structured["ok"] is True
    snapshot_without_screenshot = await mcp.call_tool(
        "browser_snapshot",
        {"session_id": "missing", "screenshot": False},
    )
    assert snapshot_without_screenshot is not None
    assert live_channel_module.get_live_channel_manager().authenticate(live_token) is None
    assert live_channel_module.get_live_channel_manager().authenticate(refreshed_live_token) is channel
    event_types = [event["type"] for event in channel.events]
    assert "tool.blocked" in event_types
    assert "tool.failed" in event_types
    assert "tool.completed" in event_types


def test_live_http_token_cors_and_human_mutation_modes(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    manager = live_channel_module.get_live_channel_manager()
    channel, token = manager.open(
        session_key="mcp:http-test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
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

        invalid_control = client.post(
            "/api/live/control",
            headers=headers,
            json={"control": "invalid"},
        )
        assert invalid_control.status_code == 400
        assert "Unsupported control mode" in invalid_control.text

        blocked = client.post(
            "/api/ui/files/write",
            headers=headers,
            json={"machine": "local", "path": "human.txt", "content": "shared"},
        )
        assert blocked.status_code == 409
        assert "Observe mode" in blocked.text

        shared = client.post(
            "/api/live/control",
            headers=headers,
            json={"control": "shared"},
        )
        assert shared.status_code == 200
        assert shared.json()["data"]["control"] == "shared"

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
