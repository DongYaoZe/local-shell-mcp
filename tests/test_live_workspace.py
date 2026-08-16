from __future__ import annotations

import asyncio
import hashlib
import subprocess
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult
from starlette.requests import Request

import local_shell_mcp.live_channel as live_channel_module
import local_shell_mcp.live_channel_routes as live_routes
import local_shell_mcp.session_runtime as session_runtime_module
import local_shell_mcp.tools as tools_module
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
from local_shell_mcp.tools import (
    _install_mcp_tool_watchdogs,
    _install_session_run_arguments,
    build_mcp,
)


def _reserve_claim(sessions: SessionRuntimeManager, session_id: str) -> dict:
    claim = sessions.claim_plan_continuation(session_id)
    assert claim is not None
    validation = sessions.validate_plan_continuation(session_id, claim["claim_id"])
    assert validation["valid"] is True
    return claim


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


@pytest.mark.asyncio
async def test_remote_only_live_workspace_rejects_local_git_shell(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    monkeypatch.setenv("LOCAL_SHELL_MCP_DISABLE_LOCAL", "true")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="Local access is disabled"):
        await live_routes._run_machine_shell(
            "local",
            "git status --short --branch",
            cwd=".",
            timeout_s=5,
            max_output_bytes=1024,
        )


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


def test_live_channel_public_state_resolves_and_tolerates_missing_logical_session(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    sessions = session_runtime_module.get_session_runtime_manager()
    started = sessions.manage("mcp:state", "user", action="start", objective="State")
    sessions.manage_plan(
        "mcp:state",
        action="start",
        objective="State",
        steps=[{"id": "work", "text": "Work"}],
    )
    channel, _ = live_channel_module.get_live_channel_manager().open(
        session_key="mcp:state",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=started["session_id"],
    )

    state = channel.public_state()
    assert state["session_id"] == started["session_id"]
    assert state["session"]["objective"] == "State"
    assert state["plan"]["status"] == "active"

    channel.logical_session_id = "s_missing"
    missing = channel.public_state()
    assert missing["session_id"] == "s_missing"
    assert missing["session"] is None
    assert missing["plan"] is None


def test_mcp_session_key_supports_http_nonweak_and_weak_sessions():
    class RequestContext:
        def __init__(self, session, headers=None):
            self.session = session
            self.request = type("Request", (), {"headers": headers})()

    class Context:
        def __init__(self, request_context):
            self.request_context = request_context

    class Mcp:
        def __init__(self, request_context):
            self.context = Context(request_context)

        def get_context(self):
            return self.context

    class NonWeakSession:
        __slots__ = ("_lsm_live_session_key",)

    class WeakSession:
        pass

    http = Mcp(RequestContext(WeakSession(), {"mcp-session-id": "transport-1"}))
    assert live_channel_module.mcp_session_key(http) == "mcp-http:transport-1"

    nonweak = Mcp(RequestContext(NonWeakSession()))
    first_nonweak = live_channel_module.mcp_session_key(nonweak)
    assert first_nonweak.startswith("mcp-session:")
    assert live_channel_module.mcp_session_key(nonweak) == first_nonweak

    weak = Mcp(RequestContext(WeakSession()))
    first_weak = live_channel_module.mcp_session_key(weak)
    assert first_weak.startswith("mcp-session:")
    assert live_channel_module.mcp_session_key(weak) == first_weak


def test_app_reattach_does_not_shorten_shared_channel_expiry():
    manager = LiveChannelManager()
    now = time.time()
    channel, token = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        parent_expires_at=now + 600,
        logical_session_id="s_task",
    )
    original_expiry = channel.expires_at

    attached, app_token = manager.open(
        session_key="mcp:app",
        subject="user",
        scopes=("shell:read",),
        parent_expires_at=now + 60,
        live_id=channel.live_id,
        logical_session_id="s_task",
        app_reattach=True,
    )

    assert attached is channel
    assert app_token != token
    assert channel.expires_at == original_expiry
    assert manager.authenticate(token) is channel
    assert manager.authenticate(app_token) is channel
    assert manager.authenticate_context(token)[2] == tuple(ALL_OAUTH_SCOPES)
    assert manager.authenticate_context(app_token)[2] == ("shell:read",)
    app_digest = manager._digest(app_token)
    manager._credentials[app_digest]["expires_at"] = now - 1
    assert manager.authenticate(app_token) is None
    assert manager.authenticate(token) is channel


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
        data={"tool": "run_shell", "call_id": "model-call"},
    )
    assert channel.events[-1]["data"]["call_id"] == "model-call"

    with pytest.raises(PermissionError, match="different principal"):
        manager.open(
            session_key="mcp:other-user",
            subject="other",
            scopes=tuple(ALL_OAUTH_SCOPES),
            live_id=channel.live_id,
        )


def test_live_workspace_logical_session_binding_replaces_old_mapping():
    manager = LiveChannelManager()
    assert manager.bind_logical_session("missing", "s_missing", "user") is None

    channel, _ = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    attached = manager.bind_logical_session("mcp:model", "s_first", "user")
    assert attached is channel
    assert channel.logical_session_id == "s_first"
    assert manager._logical_session_channels["s_first"] == channel.live_id
    assert channel.events[-1]["type"] == "session.attached"

    rebound = manager.bind_logical_session("mcp:model", "s_second", "user")
    assert rebound is channel
    assert channel.logical_session_id == "s_second"
    assert "s_first" not in manager._logical_session_channels
    assert manager._logical_session_channels["s_second"] == channel.live_id


def test_live_workspace_session_rebind_drops_prior_operational_events():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_first",
    )
    manager.publish_for_session(
        "mcp:model",
        "tool.completed",
        data={"call_id": "old-call", "tool": "file_write"},
    )
    manager.publish_for_session(
        "mcp:model",
        "human.inspected_diff",
        actor="human",
        data={"cwd": "old-task"},
    )
    old_seq = channel.seq

    rebound = manager.bind_logical_session("mcp:model", "s_second", "user")

    assert rebound is channel
    assert channel.seq > old_seq
    assert channel.logical_session_id == "s_second"
    assert [event["type"] for event in channel.events] == ["session.attached"]
    assert all(event["data"].get("call_id") != "old-call" for event in channel.events)
    manager.publish_for_session(
        "mcp:model",
        "tool.completed",
        data={"call_id": "new-call", "tool": "file_read"},
    )
    visible = manager.events_since(channel, 0)
    assert any(event["data"].get("call_id") == "new-call" for event in visible)
    assert all(event["data"].get("call_id") != "old-call" for event in visible)


def test_live_workspace_switch_does_not_rebind_channel_shared_by_another_transport():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_first",
    )
    attached, _ = manager.open(
        session_key="mcp:b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=channel.live_id,
        logical_session_id="s_first",
    )
    assert attached is channel

    assert manager.bind_logical_session("mcp:a", "s_second", "user") is None
    assert manager.active_for_session("mcp:a") is None
    assert manager.active_for_session("mcp:b") is channel
    assert channel.logical_session_id == "s_first"
    assert manager._logical_session_channels["s_first"] == channel.live_id
    assert "s_second" not in manager._logical_session_channels


def test_exclusive_model_binding_drops_superseded_transport_mapping():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:old-run",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_first",
    )
    attached, _ = manager.open(
        session_key="mcp:new-run",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=channel.live_id,
        logical_session_id="s_first",
    )
    assert attached is channel

    owner = manager.bind_logical_session(
        "mcp:new-run",
        "s_first",
        "user",
        exclusive_model_owner=True,
    )

    assert owner is channel
    assert manager.active_for_session("mcp:old-run") is None
    assert manager.active_for_session("mcp:new-run") is channel

    rebound = manager.bind_logical_session(
        "mcp:new-run",
        "s_second",
        "user",
        exclusive_model_owner=True,
    )
    assert rebound is channel
    assert channel.logical_session_id == "s_second"
    assert manager.active_for_session("mcp:new-run") is channel


def test_live_workspace_app_reattachment_follows_model_session_switch():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_first",
    )
    app_channel, _ = manager.open(
        session_key="mcp:app",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=channel.live_id,
        logical_session_id="s_first",
        app_reattach=True,
    )
    assert app_channel is channel

    rebound = manager.bind_logical_session("mcp:model", "s_second", "user")

    assert rebound is channel
    assert manager.active_for_session("mcp:model") is channel
    assert manager.active_for_session("mcp:app") is channel
    assert channel.logical_session_id == "s_second"
    assert "s_first" not in manager._logical_session_channels
    assert manager._logical_session_channels["s_second"] == channel.live_id

    reconnected, _ = manager.open(
        session_key="mcp:app-after-remount",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=channel.live_id,
        logical_session_id="s_first",
        app_reattach=True,
    )
    assert reconnected is channel
    assert reconnected.logical_session_id == "s_second"
    assert manager.active_for_session("mcp:app-after-remount") is channel


def test_live_workspace_session_switch_uses_existing_canonical_target_channel():
    manager = LiveChannelManager()
    source, _ = manager.open(
        session_key="mcp:model-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_first",
    )
    source_app, _ = manager.open(
        session_key="mcp:app-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=source.live_id,
        logical_session_id="s_first",
        app_reattach=True,
    )
    target, _ = manager.open(
        session_key="mcp:model-b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_second",
    )
    assert source_app is source
    assert target is not source

    rebound = manager.bind_logical_session("mcp:model-a", "s_second", "user")

    assert rebound is target
    assert manager.active_for_session("mcp:model-a") is target
    assert manager.active_for_session("mcp:model-b") is target
    assert manager.active_for_session("mcp:app-a") is source
    assert source.logical_session_id == "s_first"
    assert target.logical_session_id == "s_second"
    assert manager._logical_session_channels["s_first"] == source.live_id
    assert manager._logical_session_channels["s_second"] == target.live_id
    assert [
        channel.live_id
        for channel in manager._channels.values()
        if channel.logical_session_id == "s_second"
    ] == [target.live_id]

    manager.publish_for_session(
        "mcp:model-a",
        "tool.completed",
        data={"tool": "file_write", "call_id": "on-target"},
    )
    assert target.events[-1]["data"]["call_id"] == "on-target"
    assert source.events[-1]["data"].get("call_id") != "on-target"


def test_live_workspace_open_consolidates_duplicate_logical_target():
    manager = LiveChannelManager()
    unattached, _ = manager.open(
        session_key="mcp:old-app",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    target, target_token = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_target",
    )

    reattached, token = manager.open(
        session_key="mcp:new-app",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id=unattached.live_id,
        logical_session_id="s_target",
        app_reattach=True,
    )

    assert reattached is target
    assert token != target_token
    assert manager.authenticate(token) is target
    assert manager.authenticate(target_token) is target
    assert manager.active_for_session("mcp:new-app") is target
    assert unattached.logical_session_id is None
    assert manager._logical_session_channels["s_target"] == target.live_id


def test_exact_logical_binding_consumes_only_its_recovery_claim():
    manager = LiveChannelManager()
    first, _ = manager.open(
        session_key="mcp:app-a",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-a",
        logical_session_id="s_first",
        app_reattach=True,
    )
    second, _ = manager.open(
        session_key="mcp:app-b",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-b",
        logical_session_id="s_second",
        app_reattach=True,
    )
    assert len(manager._recovery_claims["user"]) == 2

    attached = manager.bind_logical_session("mcp:model-a", "s_first", "user")

    assert attached is first
    assert set(manager._recovery_claims["user"]) == {second.live_id}
    assert manager.claim_recovery_session("mcp:unrelated", "user") is second
    assert manager.active_for_session("mcp:unrelated") is second


def test_live_workspace_logical_session_binding_rejects_principal_reuse():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:reused",
        subject="alice",
        scopes=tuple(ALL_OAUTH_SCOPES),
    )
    assert manager.bind_logical_session("mcp:reused", "s_alice", "alice") is channel

    assert manager.bind_logical_session("mcp:reused", "s_bob", "bob") is None
    assert manager.active_for_session("mcp:reused") is None
    assert channel.subject == "alice"
    assert channel.logical_session_id == "s_alice"
    assert manager._logical_session_channels["s_alice"] == channel.live_id
    assert "s_bob" not in manager._logical_session_channels


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

    for credential in manager._credentials.values():
        if credential["live_id"] == first.live_id:
            credential["expires_at"] = 0
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

    batch_after = channel.seq
    empty_batch = await manager.wait_event_batch(channel, batch_after, timeout_s=0.01)
    assert empty_batch["events"] == []
    assert empty_batch["cursor"] == batch_after

    async def publish_batch_later() -> None:
        await asyncio.sleep(0.01)
        manager.publish_channel(
            channel.live_id,
            "job.batch-progress",
            actor="system",
            data={"progress": 75},
        )

    batch_publisher = asyncio.create_task(publish_batch_later())
    waited_batch = await manager.wait_event_batch(channel, batch_after, timeout_s=0.5)
    await batch_publisher
    assert waited_batch["events"][-1]["type"] == "job.batch-progress"

    for credential in manager._credentials.values():
        if credential["live_id"] == channel.live_id:
            credential["expires_at"] = 0
    channel.expires_at = 0
    assert manager.authenticate(token) is None
    assert manager.active_for_session("mcp:events") is None
    assert manager.by_id(channel.live_id) is None


@pytest.mark.parametrize("endpoint", ["/api/live/snapshot", "/api/live/events?after=0&timeout=1"])
def test_live_event_response_keeps_batch_atomic_with_session_binding(
    tmp_path, monkeypatch, endpoint
):
    _configure(tmp_path, monkeypatch, auth="none")
    sessions = session_runtime_module.get_session_runtime_manager()
    first = sessions.manage("mcp:first", "user", action="start", objective="First")
    second = sessions.manage("mcp:second", "user", action="start", objective="Second")
    manager = live_channel_module.get_live_channel_manager()
    channel, token = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=first["session_id"],
    )
    manager.publish_channel(
        channel.live_id,
        "human.action",
        actor="human",
        data={"action": "old-session", "marker": "old"},
    )
    original_get = sessions.get
    switched = False

    def switch_during_state_read(session_id, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        nonlocal switched
        state = original_get(session_id, *args, **kwargs)
        if session_id == first["session_id"] and not switched:
            switched = True
            assert manager.bind_logical_session("mcp:model", second["session_id"], "user") is channel
            manager.publish_channel(
                channel.live_id,
                "human.action",
                actor="human",
                data={"action": "new-session", "marker": "new"},
            )
        return state

    monkeypatch.setattr(sessions, "get", switch_during_state_read)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.get(endpoint, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()["data"]
    state = data["channel"] if endpoint.endswith("snapshot") else data
    assert state["session_id"] == second["session_id"]
    markers = [event["data"].get("marker") for event in data["events"]]
    assert "old" not in markers
    assert "new" in markers


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
    claim = _reserve_claim(sessions, session_id)
    sessions.report_plan_continuation(
        session_id, accepted=True, claim_id=claim["claim_id"]
    )

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
    rejected = _reserve_claim(sessions, session_id)
    assert rejected["continuation_count"] == 1
    sessions.report_plan_continuation(
        session_id,
        accepted=False,
        error="host busy",
        claim_id=rejected["claim_id"],
    )
    assert sessions.plan_state(session_id)["continuation_count"] == 1
    assert sessions.claim_plan_continuation(session_id) is None

    for expected in range(2, session_runtime_module.PLAN_MAX_CONTINUATIONS + 1):
        now[0] += max(
            session_runtime_module.PLAN_EXECUTION_LEASE_S,
            session_runtime_module.PLAN_CONTINUATION_FAILURE_BACKOFF_S,
        ) + 1
        claim = _reserve_claim(sessions, session_id)
        assert claim["continuation_count"] == expected
        assert sessions.claim_plan_continuation(session_id) is None
        sessions.report_plan_continuation(
            session_id, accepted=True, claim_id=claim["claim_id"]
        )

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
    render_tool = tools["workspace_open"]
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
    assert "session_run_id" not in reconnect_tool.inputSchema["properties"]

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

    result = await mcp.call_tool("workspace_open", {"machine": "local", "cwd": "."})
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
    assert reconnect_token != hidden["token"]
    channel = live_channel_module.get_live_channel_manager().authenticate(hidden["token"])
    assert channel is not None
    assert live_channel_module.get_live_channel_manager().authenticate(reconnect_token) is channel
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
async def test_live_workspace_reconnect_restores_persisted_logical_session(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()

    _, started = await mcp.call_tool(
        "session_manage",
        {"action": "start", "objective": "Persist across workspace recovery"},
    )
    session_id = started["data"]["session_id"]
    run_id = started["data"]["active_run"]["run_id"]
    opened = await mcp.call_tool(
        "workspace_open", {"cwd": ".", "session_run_id": run_id}
    )
    assert isinstance(opened, CallToolResult)
    old_live_id = opened.structuredContent["live_id"]
    assert opened.structuredContent["session_id"] == session_id

    attached_reconnect = await mcp.call_tool(
        "live_workspace_reconnect",
        {
            "cwd": ".",
            "live_id": old_live_id,
            "session_id": session_id,
        },
    )
    assert isinstance(attached_reconnect, CallToolResult)
    assert attached_reconnect.structuredContent["session_id"] == session_id

    monkeypatch.setattr(live_channel_module, "_MANAGER", LiveChannelManager())
    monkeypatch.setattr(
        session_runtime_module,
        "_MANAGER",
        SessionRuntimeManager(tmp_path / ".state"),
    )

    reconnected = await mcp.call_tool(
        "live_workspace_reconnect",
        {
            "cwd": ".",
            "live_id": old_live_id,
            "session_id": session_id,
        },
    )
    assert isinstance(reconnected, CallToolResult)
    assert reconnected.structuredContent["session_id"] == session_id
    recovered = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert recovered is not None
    assert recovered.logical_session_id == session_id


@pytest.mark.asyncio
async def test_live_workspace_reconnect_ignores_deleted_cached_session(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()

    _, started = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "Deleted while app sleeps"}
    )
    session_id = started["data"]["session_id"]
    run_id = started["data"]["active_run"]["run_id"]
    opened = await mcp.call_tool(
        "workspace_open", {"cwd": ".", "session_run_id": run_id}
    )
    old_live_id = opened.structuredContent["live_id"]
    channel = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert channel is not None and channel.logical_session_id == session_id

    session_manager = session_runtime_module.get_session_runtime_manager()
    session_manager.manage(
        "direct",
        "local-mcp-client",
        action="cancel",
        session_id=session_id,
        session_run_id=run_id,
        require_run_token=True,
    )
    session_manager.manage(
        "mcp:other",
        "local-mcp-client",
        action="delete",
        session_id=session_id,
    )
    assert channel.logical_session_id == session_id

    reconnected = await mcp.call_tool(
        "live_workspace_reconnect",
        {"cwd": ".", "live_id": old_live_id, "session_id": session_id},
    )

    assert reconnected.structuredContent["session_id"] is None
    assert channel.logical_session_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "terminal_event"),
    [("finish", "session.completed"), ("cancel", "session.cancelled")],
)
async def test_terminal_session_detaches_live_workspace_before_unattached_tools(
    tmp_path, monkeypatch, action, terminal_event
):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    _, started = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "Terminal boundary"}
    )
    session_id = started["data"]["session_id"]
    run_id = started["data"]["active_run"]["run_id"]
    await mcp.call_tool("workspace_open", {"cwd": ".", "session_run_id": run_id})
    channel = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert channel is not None and channel.logical_session_id == session_id

    await mcp.call_tool(
        "session_manage",
        {"action": action, "session_id": session_id, "session_run_id": run_id},
    )

    assert channel.logical_session_id is None
    _, listed = await mcp.call_tool("file_list", {"path": "."})
    assert listed["ok"] is True
    session = session_runtime_module.get_session_runtime_manager().get(
        session_id, subject="local-mcp-client"
    )
    assert session["recent_activity"][-1]["type"] == terminal_event
    assert not any(
        event["data"].get("tool") == "file_list"
        for event in session["recent_activity"]
        if event["type"].startswith("tool.")
    )


@pytest.mark.asyncio
async def test_live_workspace_reconnect_drops_attachment_after_principal_change(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    subject = ["alice"]
    monkeypatch.setattr(
        "local_shell_mcp.tools._current_principal_subject", lambda: subject[0]
    )
    mcp = build_mcp()

    _, started = await mcp.call_tool(
        "session_manage",
        {"action": "start", "objective": "Private task"},
    )
    session_id = started["data"]["session_id"]
    run_id = started["data"]["active_run"]["run_id"]
    opened = await mcp.call_tool(
        "workspace_open", {"cwd": ".", "session_run_id": run_id}
    )
    assert opened.structuredContent["session_id"] == session_id

    subject[0] = "bob"
    reconnected = await mcp.call_tool(
        "live_workspace_reconnect",
        {"cwd": "."},
    )

    assert reconnected.structuredContent["session_id"] is None
    with pytest.raises(PermissionError, match="different principal"):
        session_runtime_module.get_session_runtime_manager().get(
            session_id, subject="bob"
        )


@pytest.mark.asyncio
async def test_cancelled_tool_call_releases_logical_inflight_lease(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = session_runtime_module.get_session_runtime_manager()
    started = manager.manage("direct", "local-mcp-client", action="start", objective="Cancelable task")
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    entered = asyncio.Event()
    never = asyncio.Event()
    event_loop_thread = threading.get_ident()
    begin_threads: list[int] = []
    finish_threads: list[int] = []
    original_begin = manager.begin_tool_call
    original_finish = manager.finish_tool_call

    def observed_begin(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        begin_threads.append(threading.get_ident())
        return original_begin(*args, **kwargs)

    def observed_finish(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        finish_threads.append(threading.get_ident())
        return original_finish(*args, **kwargs)

    monkeypatch.setattr(manager, "begin_tool_call", observed_begin)
    monkeypatch.setattr(manager, "finish_tool_call", observed_finish)
    mcp = FastMCP("cancel-test")

    @mcp.tool()
    async def wait_forever() -> dict[str, bool]:
        entered.set()
        await never.wait()
        return {"ok": True}

    _install_session_run_arguments(mcp)
    _install_mcp_tool_watchdogs(mcp)
    task = asyncio.create_task(
        mcp.call_tool("wait_forever", {"session_run_id": run_id})
    )
    await asyncio.wait_for(entered.wait(), timeout=1)
    assert manager._sessions[session_id].in_flight_calls

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert manager._sessions[session_id].in_flight_calls == {}
    assert begin_threads and all(thread_id != event_loop_thread for thread_id in begin_threads)
    assert finish_threads and all(thread_id != event_loop_thread for thread_id in finish_threads)


@pytest.mark.asyncio
async def test_cancelled_thread_mutation_holds_logical_lease_until_worker_finishes(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = session_runtime_module.get_session_runtime_manager()
    started = manager.manage(
        "direct", "local-mcp-client", action="start", objective="Thread mutation"
    )
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    entered = threading.Event()
    release = threading.Event()
    from local_shell_mcp.fs_ops import write_text as real_write_text

    def blocking_write_text(path, content, overwrite=True):  # noqa: ANN001, ANN202
        entered.set()
        assert release.wait(timeout=5)
        return real_write_text(path, content, overwrite)

    monkeypatch.setattr("local_shell_mcp.tools.write_text", blocking_write_text)
    mcp = build_mcp()
    task = asyncio.create_task(
        mcp.call_tool(
            "file_write",
            {
                "path": "threaded.txt",
                "content": "completed after cancellation",
                "session_run_id": run_id,
            },
        )
    )
    assert await asyncio.to_thread(entered.wait, 1)
    assert manager._sessions[session_id].in_flight_calls

    task.cancel()
    await asyncio.sleep(0.05)
    assert not task.done()
    assert manager._sessions[session_id].in_flight_calls
    with pytest.raises(ValueError, match="tool calls are still in flight"):
        manager.manage(
            "mcp:takeover",
            "local-mcp-client",
            action="resume",
            session_id=session_id,
            takeover=True,
        )

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert manager._sessions[session_id].in_flight_calls == {}
    assert (tmp_path / "threaded.txt").read_text(encoding="utf-8") == "completed after cancellation"


@pytest.mark.asyncio
async def test_predispatch_failure_releases_logical_inflight_lease(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = session_runtime_module.get_session_runtime_manager()
    started = manager.manage(
        "direct", "local-mcp-client", action="start", objective="Setup failure"
    )
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    mcp = build_mcp()

    def fail_start_audit(event, **kwargs):  # noqa: ANN001, ANN003, ANN202
        if event == "mcp_tool_call_start":
            raise OSError("audit volume unavailable")

    monkeypatch.setattr("local_shell_mcp.tools.audit", fail_start_audit)
    with pytest.raises(Exception, match="audit volume unavailable"):
        await mcp.call_tool(
            "file_write",
            {
                "path": "never.txt",
                "content": "must not run",
                "session_run_id": run_id,
            },
        )

    assert manager._sessions[session_id].in_flight_calls == {}
    assert not (tmp_path / "never.txt").exists()


@pytest.mark.asyncio
async def test_lease_heartbeat_survives_renewal_audit_failure(monkeypatch):
    calls = 0

    class FlakyManager:
        def renew_tool_call(self, lease):  # noqa: ANN001, ANN201
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("state backend unavailable")
            return False

    async def no_wait(_seconds):  # noqa: ANN001, ANN202
        return None

    def fail_audit(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
        raise OSError("audit backend unavailable")

    monkeypatch.setattr(tools_module.asyncio, "sleep", no_wait)
    monkeypatch.setattr(tools_module, "audit", fail_audit)

    await tools_module._renew_session_tool_lease(
        FlakyManager(),
        {"session_id": "s_test", "run_id": "r_test", "call_id": "call-test"},
        tool_name="file_write",
        call_id="call-test",
    )

    assert calls == 2


@pytest.mark.asyncio
async def test_completed_tool_retries_durable_lease_cleanup(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = session_runtime_module.get_session_runtime_manager()
    started = manager.manage(
        "direct", "local-mcp-client", action="start", objective="Cleanup retry"
    )
    session_id = started["session_id"]
    run_id = started["active_run"]["run_id"]
    lease = manager.begin_tool_call(
        "direct",
        "call-cleanup",
        expected_run_id=run_id,
        subject="local-mcp-client",
        data={"tool": "write_file"},
    )
    assert lease is not None
    original_save = manager._save_locked
    failures_left = 2

    def fail_completion_writes(session):  # noqa: ANN001, ANN202
        nonlocal failures_left
        if failures_left:
            failures_left -= 1
            raise OSError("state backend temporarily unavailable")
        return original_save(session)

    async def no_wait(_seconds):  # noqa: ANN001, ANN202
        return None

    monkeypatch.setattr(manager, "_save_locked", fail_completion_writes)
    monkeypatch.setattr(tools_module.asyncio, "sleep", no_wait)
    await tools_module._finish_session_tool_activity(
        manager,
        lease,
        "tool.completed",
        {"call_id": "call-cleanup", "ok": True, "tool": "write_file"},
        tool_name="write_file",
        call_id="call-cleanup",
        stage="completed",
    )
    pending = list(tools_module._PENDING_SESSION_LEASE_CLEANUPS)
    assert pending
    await asyncio.gather(*pending)

    restored = SessionRuntimeManager(tmp_path / ".state")
    restored.get(session_id, subject="local-mcp-client")
    assert restored._in_flight_count_locked(session_id) == 0


@pytest.mark.asyncio
async def test_mcp_run_lease_blocks_stale_same_transport_agent(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()

    _, started = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "Lease protected task"}
    )
    session_id = started["data"]["session_id"]
    first_run_id = started["data"]["active_run"]["run_id"]
    _, resumed = await mcp.call_tool(
        "session_manage",
        {"action": "resume", "session_id": session_id, "takeover": True},
    )
    second_run_id = resumed["data"]["active_run"]["run_id"]
    assert second_run_id != first_run_id

    with pytest.raises(Exception, match="superseded"):
        await mcp.call_tool(
            "file_write",
            {
                "path": "stale.txt",
                "content": "must not be written",
                "session_run_id": first_run_id,
            },
        )
    assert not (tmp_path / "stale.txt").exists()

    _, written = await mcp.call_tool(
        "file_write",
        {
            "path": "current.txt",
            "content": "current run",
            "session_run_id": second_run_id,
        },
    )
    assert written["ok"] is True
    assert (tmp_path / "current.txt").read_text(encoding="utf-8") == "current run"


@pytest.mark.asyncio
async def test_session_get_refreshes_attached_plan_agent_activity(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    _, started = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "Inspect without takeover"}
    )
    session_id = started["data"]["session_id"]
    run_id = started["data"]["active_run"]["run_id"]
    await mcp.call_tool(
        "plan_manage",
        {
            "action": "start",
            "session_run_id": run_id,
            "objective": "Inspect without takeover",
            "steps": [{"id": "inspect", "text": "Inspect"}],
        },
    )
    manager = session_runtime_module.get_session_runtime_manager()
    logical = manager._sessions[session_id]
    assert logical.plan is not None
    old_activity = time.time() - session_runtime_module.PLAN_EXECUTION_LEASE_S - 5
    logical.plan.last_agent_activity = old_activity
    manager._save_locked(logical)

    _, fetched = await mcp.call_tool(
        "session_manage", {"action": "get", "session_id": session_id}
    )

    assert fetched["data"]["session_id"] == session_id
    current = manager.plan_state(session_id)
    assert current is not None
    assert current["last_agent_activity"] > old_activity
    assert current["continuation_due"] is False
    assert manager.claim_plan_continuation(session_id, subject="local-mcp-client") is None


@pytest.mark.asyncio
async def test_explicit_resume_binds_live_channel_by_resolved_logical_session(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    session_manager = session_runtime_module.get_session_runtime_manager()
    first = session_manager.manage(
        "old-a", "local-mcp-client", action="start", objective="First"
    )
    second = session_manager.manage(
        "old-b", "local-mcp-client", action="start", objective="Second"
    )
    live_manager = live_channel_module.get_live_channel_manager()
    first_channel, _ = live_manager.open(
        session_key="app-a",
        subject="local-mcp-client",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-a",
        logical_session_id=first["session_id"],
    )
    second_channel, _ = live_manager.open(
        session_key="app-b",
        subject="local-mcp-client",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="stale-b",
        logical_session_id=second["session_id"],
    )
    assert live_manager.claim_recovery_session("direct", "local-mcp-client") is None

    mcp = build_mcp()
    with pytest.raises(Exception, match="No logical session is attached"):
        await mcp.call_tool(
            "file_write",
            {
                "path": "must-not-write.txt",
                "content": "no",
                "session_run_id": first["active_run"]["run_id"],
            },
        )

    _, resumed = await mcp.call_tool(
        "session_manage",
        {
            "action": "resume",
            "session_id": first["session_id"],
            "takeover": True,
        },
    )
    resumed_run_id = resumed["data"]["active_run"]["run_id"]
    await mcp.call_tool(
        "file_write",
        {
            "path": "recovered.txt",
            "content": "ok",
            "session_run_id": resumed_run_id,
        },
    )

    assert not (tmp_path / "must-not-write.txt").exists()
    assert live_manager.active_for_session("direct") is first_channel
    assert any(
        event["type"] == "tool.completed" and event["data"].get("tool") == "file_write"
        for event in first_channel.events
    )
    assert not any(
        event["type"] == "tool.completed" and event["data"].get("tool") == "file_write"
        for event in second_channel.events
    )


@pytest.mark.asyncio
async def test_session_manage_rebind_does_not_split_ephemeral_tool_lifecycle(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    _, first = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "First task"}
    )
    first_id = first["data"]["session_id"]
    first_run_id = first["data"]["active_run"]["run_id"]
    opened = await mcp.call_tool(
        "workspace_open", {"cwd": ".", "session_run_id": first_run_id}
    )
    assert opened.structuredContent["session_id"] == first_id

    session_manager = session_runtime_module.get_session_runtime_manager()
    second = session_manager.manage(
        "mcp:second-owner",
        "local-mcp-client",
        action="start",
        objective="Second task",
    )
    live_manager = live_channel_module.get_live_channel_manager()
    first_channel = live_manager.active_for_session("direct")
    assert first_channel is not None
    second_channel, _ = live_manager.open(
        session_key="mcp:second-owner",
        subject="local-mcp-client",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=second["session_id"],
    )

    _, resumed = await mcp.call_tool(
        "session_manage",
        {
            "action": "resume",
            "session_id": second["session_id"],
            "takeover": True,
        },
    )
    assert resumed["data"]["session_id"] == second["session_id"]
    assert live_manager.active_for_session("direct") is second_channel

    for channel in (first_channel, second_channel):
        assert not any(
            event["type"].startswith("tool.")
            and event["data"].get("tool") == "session_manage"
            for event in channel.events
        )


@pytest.mark.asyncio
async def test_tool_does_not_execute_when_start_lease_persistence_fails(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    _, started = await mcp.call_tool(
        "session_manage", {"action": "start", "objective": "Persist activity"}
    )
    run_id = started["data"]["active_run"]["run_id"]
    manager = session_runtime_module.get_session_runtime_manager()

    def fail_save(_session):
        raise OSError("state volume full")

    monkeypatch.setattr(manager, "_save_locked", fail_save)
    with pytest.raises(Exception, match="refusing to execute"):
        await mcp.call_tool(
            "file_write",
            {
                "path": "completed.txt",
                "content": "must not be written",
                "session_run_id": run_id,
            },
        )
    assert not (tmp_path / "completed.txt").exists()


@pytest.mark.asyncio
async def test_live_workspace_keeps_model_and_human_mutations_collaborative(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    mcp = build_mcp()
    result = await mcp.call_tool("workspace_open", {"cwd": "."})
    assert isinstance(result, CallToolResult)
    live_token = result.meta["local-shell-mcp/live"]["token"]
    channel = live_channel_module.get_live_channel_manager().active_for_session("direct")
    assert channel is not None

    reopened = await mcp.call_tool("workspace_open", {"cwd": "."})
    assert isinstance(reopened, CallToolResult)
    refreshed_live_token = reopened.meta["local-shell-mcp/live"]["token"]
    assert refreshed_live_token != live_token
    await mcp.call_tool("file_write", {"path": "shared.txt", "content": "shared"})
    assert (tmp_path / "shared.txt").read_text(encoding="utf-8") == "shared"
    _, structured = await mcp.call_tool("file_list", {"path": "."})
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
        assert snapshot.json()["data"]["channel"]["session"]["session_id"] == logical["session_id"]
        assert snapshot.json()["data"]["channel"]["session"]["objective"] == "Exercise human goal controls"

        bootstrap = client.get("/api/ui/bootstrap", headers=headers)
        assert bootstrap.status_code == 200

        events = client.get("/api/live/events?after=0&timeout=1", headers=headers)
        assert events.status_code == 200
        assert events.json()["data"]["events"]
        assert events.json()["data"]["session"]["session_id"] == logical["session_id"]

        invalid_cursor = client.get("/api/live/events?after=not-a-number", headers=headers)
        assert invalid_cursor.status_code == 400
        assert invalid_cursor.json()["message"] == "Invalid event cursor"

        session_manager.manage_plan(
            "mcp:http-test",
            action="start",
            objective="Exercise human goal controls",
            steps=[{"id": "work", "text": "Do the work"}],
        )
        not_due = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "claim"},
        )
        assert not_due.status_code == 200
        assert not_due.json()["data"]["claimed"] is False

        logical_state = session_manager._sessions[logical["session_id"]]
        assert logical_state.plan is not None
        logical_state.plan.last_agent_activity -= session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
        claimed = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "claim"},
        )
        assert claimed.status_code == 200
        assert claimed.json()["data"]["claimed"] is True
        claim_id = claimed.json()["data"]["claim_id"]
        assert claim_id
        validated = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "validate", "claim_id": claim_id},
        )
        assert validated.status_code == 200
        assert validated.json()["data"]["valid"] is True
        reported = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "report", "claim_id": claim_id, "accepted": True},
        )
        assert reported.status_code == 200
        assert reported.json()["data"]["plan"]["continuation_count"] == 1
        invalid_continuation = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "invalid"},
        )
        assert invalid_continuation.status_code == 400

        logical_state.plan.last_agent_activity -= session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
        stale_claim = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "claim"},
        )
        stale_claim_id = stale_claim.json()["data"]["claim_id"]
        paused = client.post(
            "/api/live/plan",
            headers=headers,
            json={"action": "pause", "note": "Auto continuation cancelled by user"},
        )
        assert paused.status_code == 200
        assert paused.json()["data"]["plan"]["status"] == "blocked"
        assert paused.json()["data"]["plan"]["note"] == "Auto continuation cancelled by user"
        invalidated = client.post(
            "/api/live/plan/continuation",
            headers=headers,
            json={"action": "validate", "claim_id": stale_claim_id},
        )
        assert invalidated.status_code == 200
        assert invalidated.json()["data"]["valid"] is False
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
        invalid_plan = client.post(
            "/api/live/plan", headers=headers, json={"action": "invalid"}
        )
        assert invalid_plan.status_code == 400

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


def test_human_plan_action_does_not_publish_across_session_rebind(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    session_manager = session_runtime_module.get_session_runtime_manager()
    first = session_manager.manage(
        "mcp:http-first", "user", action="start", objective="First task"
    )
    second = session_manager.manage(
        "mcp:http-second", "user", action="start", objective="Second task"
    )
    session_manager.manage_plan(
        "mcp:http-first",
        action="start",
        objective="First task",
        steps=[{"id": "first", "text": "First"}],
    )
    session_manager.manage_plan(
        "mcp:http-second",
        action="start",
        objective="Second task",
        steps=[{"id": "second", "text": "Second"}],
    )
    live_manager = live_channel_module.get_live_channel_manager()
    channel, token = live_manager.open(
        session_key="mcp:http-first",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=first["session_id"],
    )
    original_manage = session_manager.manage_plan_for_session

    def rebind_after_plan_action(session_id, **kwargs):  # noqa: ANN001, ANN003, ANN202
        result = original_manage(session_id, **kwargs)
        assert live_manager.bind_logical_session(
            "mcp:http-first", second["session_id"], "user"
        ) is channel
        return result

    monkeypatch.setattr(session_manager, "manage_plan_for_session", rebind_after_plan_action)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.post(
            "/api/live/plan",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "pause", "note": "Pause the first task"},
        )

    assert response.status_code == 409
    assert "binding changed" in response.json()["message"]
    assert channel.logical_session_id == second["session_id"]
    assert session_manager.plan_state(first["session_id"])["status"] == "blocked"
    assert session_manager.plan_state(second["session_id"])["status"] == "active"
    assert not any(event["type"] == "plan.blocked" for event in channel.events)


def test_continuation_validation_is_pinned_to_live_session_binding(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    session_manager = session_runtime_module.get_session_runtime_manager()
    first = session_manager.manage(
        "mcp:first", "user", action="start", objective="First continuation"
    )
    second = session_manager.manage(
        "mcp:second", "user", action="start", objective="Second continuation"
    )
    session_manager.manage_plan(
        "mcp:first",
        action="start",
        objective="First continuation",
        steps=[{"id": "work", "text": "Work"}],
    )
    first_state = session_manager._sessions[first["session_id"]]
    assert first_state.plan is not None
    first_state.plan.last_agent_activity -= session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    claim = session_manager.claim_plan_continuation(first["session_id"], subject="user")
    assert claim is not None

    live_manager = live_channel_module.get_live_channel_manager()
    channel, token = live_manager.open(
        session_key="mcp:live",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=first["session_id"],
    )
    original_validate = session_manager.validate_plan_continuation

    def validate_then_rebind(session_id, claim_id, **kwargs):  # noqa: ANN001, ANN003, ANN202
        result = original_validate(session_id, claim_id, **kwargs)
        assert result["valid"] is True
        assert live_manager.bind_logical_session(
            "mcp:live",
            second["session_id"],
            "user",
            exclusive_model_owner=True,
        ) is channel
        return result

    monkeypatch.setattr(
        session_manager, "validate_plan_continuation", validate_then_rebind
    )
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.post(
            "/api/live/plan/continuation",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "validate", "claim_id": claim["claim_id"]},
        )

    assert response.status_code == 409
    assert "binding changed" in response.json()["message"]
    assert channel.logical_session_id == second["session_id"]
    abandoned = session_manager.plan_state(first["session_id"])
    assert abandoned["continuation_pending"] is False
    assert abandoned["continuation_reserved"] is False
    assert abandoned["continuation_count"] == 1


def test_continuation_claim_is_abandoned_when_live_session_rebinds(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="oauth")
    session_manager = session_runtime_module.get_session_runtime_manager()
    first = session_manager.manage(
        "mcp:first", "user", action="start", objective="First continuation"
    )
    second = session_manager.manage(
        "mcp:second", "user", action="start", objective="Second continuation"
    )
    session_manager.manage_plan(
        "mcp:first",
        action="start",
        objective="First continuation",
        steps=[{"id": "work", "text": "Work"}],
    )
    first_state = session_manager._sessions[first["session_id"]]
    assert first_state.plan is not None
    first_state.plan.last_agent_activity -= session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    live_manager = live_channel_module.get_live_channel_manager()
    channel, token = live_manager.open(
        session_key="mcp:live",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=first["session_id"],
    )
    original_claim = session_manager.claim_plan_continuation

    def claim_then_rebind(session_id, **kwargs):  # noqa: ANN001, ANN003, ANN202
        result = original_claim(session_id, **kwargs)
        assert result is not None
        assert live_manager.bind_logical_session(
            "mcp:live",
            second["session_id"],
            "user",
            exclusive_model_owner=True,
        ) is channel
        return result

    monkeypatch.setattr(session_manager, "claim_plan_continuation", claim_then_rebind)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.post(
            "/api/live/plan/continuation",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "claim"},
        )

    assert response.status_code == 409
    abandoned = session_manager.plan_state(first["session_id"])
    assert abandoned["continuation_pending"] is False
    assert abandoned["continuation_count"] == 0


def test_failed_continuation_report_releases_old_session_claim_after_rebind(
    tmp_path, monkeypatch
):
    _configure(tmp_path, monkeypatch, auth="oauth")
    session_manager = session_runtime_module.get_session_runtime_manager()
    first = session_manager.manage(
        "mcp:first", "user", action="start", objective="First continuation"
    )
    second = session_manager.manage(
        "mcp:second", "user", action="start", objective="Second continuation"
    )
    session_manager.manage_plan(
        "mcp:first",
        action="start",
        objective="First continuation",
        steps=[{"id": "work", "text": "Work"}],
    )
    first_state = session_manager._sessions[first["session_id"]]
    assert first_state.plan is not None
    first_state.plan.last_agent_activity -= session_runtime_module.PLAN_EXECUTION_LEASE_S + 1
    claim = session_manager.claim_plan_continuation(first["session_id"], subject="user")
    assert claim is not None
    validated = session_manager.validate_plan_continuation(
        first["session_id"], claim["claim_id"], subject="user"
    )
    assert validated["valid"] is True

    live_manager = live_channel_module.get_live_channel_manager()
    channel, token = live_manager.open(
        session_key="mcp:live",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id=first["session_id"],
    )

    def fail_report_after_rebind(session_id, **kwargs):  # noqa: ANN001, ANN003, ANN202
        assert session_id == first["session_id"]
        assert live_manager.bind_logical_session(
            "mcp:live",
            second["session_id"],
            "user",
            exclusive_model_owner=True,
        ) is channel
        raise OSError("report backend unavailable")

    monkeypatch.setattr(session_manager, "report_plan_continuation", fail_report_after_rebind)
    app = _build_mcp_http_app(build_mcp())
    with TestClient(app, base_url="http://testserver") as client:
        response = client.post(
            "/api/live/plan/continuation",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "report", "claim_id": claim["claim_id"], "accepted": True},
        )

    assert response.status_code == 409
    abandoned = session_manager.plan_state(first["session_id"])
    assert abandoned["continuation_pending"] is False
    assert abandoned["continuation_reserved"] is False
    assert abandoned["continuation_count"] == 1


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
        no_session_continuation = client.post(
            "/api/live/plan/continuation",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "claim"},
        )
        no_session_plan = client.post(
            "/api/live/plan",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "pause"},
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
    assert no_session_continuation.status_code == 200
    assert no_session_continuation.json()["data"] == {
        "claimed": False,
        "plan": None,
        "session_id": None,
    }
    assert no_session_plan.status_code == 409
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
        return {
            "events": [],
            "session_id": channel.logical_session_id,
            "binding_generation": channel.binding_generation,
            "seq": channel.seq,
            "cursor": after,
        }

    monkeypatch.setattr(manager, "wait_event_batch", empty_wait)
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
    assert "workspace_open" not in tools
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
    assert "workspace_open" not in tools
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


@pytest.mark.asyncio
async def test_live_events_detaches_channel_when_durable_session_disappears(monkeypatch):
    manager = LiveChannelManager()
    channel, token = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_deleted_elsewhere",
    )

    class MissingSessionManager:
        def get(self, session_id, *, subject=None):  # noqa: ANN001, ANN201
            raise ValueError(f"Unknown logical session: {session_id}")

    monkeypatch.setattr(live_routes, "get_live_channel_manager", lambda: manager)
    monkeypatch.setattr(
        live_routes, "get_session_runtime_manager", lambda: MissingSessionManager()
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/live/events",
            "query_string": b"after=0&timeout=1",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
        }
    )
    request.state.principal = Principal(
        email=None,
        subject="user",
        claims={"scope": " ".join(ALL_OAUTH_SCOPES), "live_id": channel.live_id},
    )

    response = await live_routes.live_events(request)

    assert response.status_code == 200
    assert channel.logical_session_id is None
    assert "s_deleted_elsewhere" not in manager._logical_session_channels


def test_live_workspace_stale_live_id_falls_back_to_logical_channel():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:first",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_task",
    )

    reattached, _ = manager.open(
        session_key="mcp:second",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        live_id="expired-live-id",
        logical_session_id="s_task",
    )

    assert reattached is channel
    assert manager.active_for_session("mcp:second") is channel
    assert len(manager._channels) == 1


def test_live_workspace_detaches_deleted_logical_session():
    manager = LiveChannelManager()
    channel, _ = manager.open(
        session_key="mcp:model",
        subject="user",
        scopes=tuple(ALL_OAUTH_SCOPES),
        logical_session_id="s_deleted",
    )

    detached = manager.detach_logical_session("s_deleted")

    assert detached == [channel]
    assert channel.logical_session_id is None
    assert "s_deleted" not in manager._logical_session_channels
    assert channel.events[-1]["type"] == "session.detached"



@pytest.mark.asyncio
async def test_live_workspace_session_lookups_run_off_event_loop(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch, auth="none")
    manager = session_runtime_module.get_session_runtime_manager()
    target = manager.manage(
        "other-transport",
        "local-mcp-client",
        action="start",
        objective="Reconnect target",
    )
    loop_thread = threading.get_ident()
    current_threads: list[int] = []
    get_threads: list[int] = []
    original_current = manager.current_session_id
    original_get = manager.get

    def observed_current(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        current_threads.append(threading.get_ident())
        return original_current(*args, **kwargs)

    def observed_get(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        get_threads.append(threading.get_ident())
        return original_get(*args, **kwargs)

    monkeypatch.setattr(manager, "current_session_id", observed_current)
    monkeypatch.setattr(manager, "get", observed_get)
    mcp = build_mcp()
    await mcp.call_tool(
        "live_workspace_reconnect",
        {"cwd": ".", "session_id": target["session_id"]},
    )

    assert current_threads and all(thread_id != loop_thread for thread_id in current_threads)
    assert get_threads and all(thread_id != loop_thread for thread_id in get_threads)
