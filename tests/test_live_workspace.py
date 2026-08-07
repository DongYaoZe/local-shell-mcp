from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.types import CallToolResult
from starlette.requests import Request

import local_shell_mcp.live_workspace as live_module
import local_shell_mcp.live_workspace_routes as live_routes
from local_shell_mcp.auth import Principal
from local_shell_mcp.live_workspace import (
    LIVE_EVENT_LIMIT,
    LIVE_RESOURCE_MIME,
    LIVE_RESOURCE_URI,
    HumanCollaborationRequiredError,
    HumanControlActiveError,
    LiveWorkspaceManager,
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
    monkeypatch.setattr(live_module, "_MANAGER", LiveWorkspaceManager())


def test_live_workspace_tokens_rotate_and_events_are_bounded():
    manager = LiveWorkspaceManager()
    workspace, first_token = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    same_workspace, second_token = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    assert same_workspace.workspace_id == workspace.workspace_id
    assert first_token != second_token
    assert manager.authenticate(first_token) is None
    assert manager.authenticate(second_token) is workspace

    for index in range(LIVE_EVENT_LIMIT + 50):
        manager.publish_workspace(
            workspace.workspace_id,
            "test.event",
            actor="system",
            data={"index": index},
        )

    assert len(workspace.events) == LIVE_EVENT_LIMIT
    assert workspace.events[-1]["data"]["index"] == LIVE_EVENT_LIMIT + 49
    assert workspace.events[0]["seq"] == workspace.seq - LIVE_EVENT_LIMIT + 1


@pytest.mark.asyncio
async def test_live_workspace_expiry_publish_and_wait_paths():
    manager = LiveWorkspaceManager()
    workspace, token = manager.open(
        session_key="mcp:events",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    assert manager.authenticate(None) is None
    assert manager.publish_workspace("missing", "ignored", actor="system") is None

    immediate = await manager.wait_events(workspace, 0, timeout_s=0.1)
    assert immediate and immediate[0]["type"] == "workspace.opened"

    after = workspace.seq
    assert await manager.wait_events(workspace, after, timeout_s=0.01) == []

    async def publish_later() -> None:
        await asyncio.sleep(0.01)
        manager.publish_workspace(
            workspace.workspace_id,
            "job.progress",
            actor="system",
            data={"progress": 50},
        )

    publisher = asyncio.create_task(publish_later())
    waited = await manager.wait_events(workspace, after, timeout_s=0.5)
    await publisher
    assert waited[-1]["type"] == "job.progress"

    workspace.expires_at = 0
    assert manager.authenticate(token) is None
    assert manager.active_for_session("mcp:events") is None
    assert manager.by_id(workspace.workspace_id) is None


def test_live_workspace_rejects_invalid_control_and_missing_workspace():
    manager = LiveWorkspaceManager()
    workspace, _ = manager.open(
        session_key="mcp:control-errors",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    with pytest.raises(ValueError, match="Unsupported control mode"):
        manager.set_control(workspace, "invalid")
    with pytest.raises(HumanCollaborationRequiredError, match="no longer available"):
        manager.require_human_mutation_allowed("missing")


def test_mcp_session_key_uses_request_session_identity():
    session = object()

    class FakeMcp:
        @staticmethod
        def get_context():
            return type(
                "Context",
                (),
                {"request_context": type("RequestContext", (), {"session": session})()},
            )()

    assert live_module.mcp_session_key(FakeMcp()) == f"mcp:{id(session):x}"


def test_control_modes_enforce_both_sides():
    manager = LiveWorkspaceManager()
    workspace, _ = manager.open(
        session_key="mcp:test",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )

    with pytest.raises(HumanCollaborationRequiredError):
        manager.require_human_mutation_allowed(workspace.workspace_id)

    manager.set_control(workspace, "shared")
    manager.require_human_mutation_allowed(workspace.workspace_id)
    manager.require_agent_mutation_allowed("mcp:test", "write_file")

    manager.set_control(workspace, "human")
    manager.require_human_mutation_allowed(workspace.workspace_id)
    with pytest.raises(HumanControlActiveError):
        manager.require_agent_mutation_allowed("mcp:test", "write_file")

    manager.set_control(workspace, "agent")
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
    assert render_tool.meta["securitySchemes"][0]["scopes"] == list(ALL_OAUTH_SCOPES)
    assert render_tool.outputSchema["title"] == "LiveWorkspaceResult"

    resources = {str(resource.uri): resource for resource in await mcp.list_resources()}
    resource = resources[LIVE_RESOURCE_URI]
    assert resource.mimeType == LIVE_RESOURCE_MIME
    assert resource.meta["ui"]["csp"]["connectDomains"] == ["https://lsm.example.test"]
    assert resource.meta["ui"]["permissions"] == {"clipboardWrite": {}}

    result = await mcp.call_tool("open_live_workspace", {"machine": "local", "cwd": "."})
    assert isinstance(result, CallToolResult)
    assert result.structuredContent["workspace_id"]
    assert "token" not in result.structuredContent
    hidden = result.meta["local-shell-mcp/live"]
    assert hidden["token"]
    assert hidden["apiBase"] == "https://lsm.example.test"

    contents = list(await mcp.read_resource(LIVE_RESOURCE_URI))
    assert contents[0].mime_type == LIVE_RESOURCE_MIME
    assert "local-shell-mcp-live-workspace" in str(contents[0].content)


@pytest.mark.asyncio
async def test_human_takeover_blocks_model_mutation_but_not_reads(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    result = await mcp.call_tool("open_live_workspace", {"cwd": "."})
    assert isinstance(result, CallToolResult)
    workspace = live_module.get_live_workspace_manager().active_for_session("direct")
    assert workspace is not None
    live_module.get_live_workspace_manager().set_control(workspace, "human")

    with pytest.raises(Exception, match="human takeover mode"):
        await mcp.call_tool("write_file", {"path": "blocked.txt", "content": "blocked"})

    assert not (tmp_path / "blocked.txt").exists()
    _, structured = await mcp.call_tool("list_files", {"path": "."})
    assert structured["ok"] is True
    event_types = [event["type"] for event in workspace.events]
    assert "tool.blocked" in event_types
    assert "tool.failed" in event_types
    assert "tool.completed" in event_types


def test_live_http_token_cors_and_human_mutation_modes(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    manager = live_module.get_live_workspace_manager()
    workspace, token = manager.open(
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
        assert snapshot.json()["data"]["workspace"]["workspace_id"] == workspace.workspace_id

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
        (tmp_path / "tracked.txt").write_text("after\n", encoding="utf-8")
        git = client.get("/api/live/git?cwd=.", headers=headers)
        assert git.status_code == 200
        git_data = git.json()["data"]
        assert "tracked.txt" in git_data["status"]["stdout"]
        assert "before" in git_data["diff"]["stdout"]
        assert any(
            event["type"] == "human.inspected_diff" for event in workspace.events
        )

        # A live token is deliberately not valid for the MCP transport itself.
        mcp_attempt = client.post(
            "/mcp",
            headers={**headers, "Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        assert mcp_attempt.status_code in {401, 403}


def test_live_route_helpers_reject_missing_or_expired_workspace(monkeypatch):
    request = Request({"type": "http", "method": "GET", "path": "/api/live/snapshot", "headers": []})
    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": "shell:read"},
    )
    with pytest.raises(Exception, match="live-workspace token"):
        live_routes._live_workspace(request)

    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": "shell:read", "live_workspace_id": "expired"},
    )
    monkeypatch.setattr(live_routes, "get_live_workspace_manager", lambda: LiveWorkspaceManager())
    with pytest.raises(Exception, match="Live workspace expired"):
        live_routes._live_workspace(request)


def test_live_route_principal_falls_back_to_request_verification(monkeypatch):
    request = Request({"type": "http", "method": "GET", "path": "/api/live/snapshot", "headers": []})
    expected = Principal(email=None, subject="verified", claims={})
    monkeypatch.setattr(live_routes, "current_principal", lambda: None)
    monkeypatch.setattr(live_routes, "verify_request", lambda _request: expected)
    assert live_routes._principal(request) is expected
