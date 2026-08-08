from __future__ import annotations

import asyncio
import hashlib
import secrets
import threading
import time
import uuid
import weakref
from collections import deque
from dataclasses import dataclass, field
from typing import Any

LIVE_RESOURCE_URI = "ui://local-shell-mcp/live-workspace.html"
LIVE_RESOURCE_MIME = "text/html;profile=mcp-app"
LIVE_API_PREFIX = "/api/live"
LIVE_TOKEN_TTL_S = 12 * 60 * 60
LIVE_EVENT_LIMIT = 2_000
LIVE_EVENT_BATCH = 300
LIVE_LONG_POLL_S = 25.0
CONTROL_MODES = frozenset({"agent", "shared", "human"})
_SESSION_KEYS: weakref.WeakKeyDictionary[Any, str] = weakref.WeakKeyDictionary()
_SESSION_KEYS_LOCK = threading.Lock()


class HumanControlActiveError(RuntimeError):
    pass


class HumanCollaborationRequiredError(RuntimeError):
    pass


@dataclass(slots=True)
class LiveWorkspace:
    workspace_id: str
    session_key: str
    subject: str
    scopes: tuple[str, ...]
    token_digest: str
    created_at: float
    expires_at: float
    control: str = "agent"
    seq: int = 0
    events: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=LIVE_EVENT_LIMIT)
    )
    signal: asyncio.Event = field(default_factory=asyncio.Event)

    def public_state(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "control": self.control,
            "seq": self.seq,
        }


class LiveWorkspaceManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workspaces: dict[str, LiveWorkspace] = {}
        self._session_workspaces: dict[str, str] = {}

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _prune_locked(self, now: float | None = None) -> None:
        current = time.time() if now is None else now
        expired = [
            workspace_id
            for workspace_id, workspace in self._workspaces.items()
            if workspace.expires_at <= current
        ]
        for workspace_id in expired:
            self._workspaces.pop(workspace_id, None)
        if expired:
            expired_ids = set(expired)
            self._session_workspaces = {
                session_key: workspace_id
                for session_key, workspace_id in self._session_workspaces.items()
                if workspace_id not in expired_ids
            }

    def open(
        self,
        *,
        session_key: str,
        subject: str,
        scopes: tuple[str, ...],
        parent_expires_at: float | None = None,
        workspace_id: str | None = None,
    ) -> tuple[LiveWorkspace, str]:
        now = time.time()
        expires_at = now + LIVE_TOKEN_TTL_S
        if parent_expires_at is not None:
            expires_at = min(expires_at, parent_expires_at)
        token = secrets.token_urlsafe(32)
        digest = self._digest(token)
        with self._lock:
            self._prune_locked(now)
            session_workspace_id = self._session_workspaces.get(session_key)
            workspace = self._workspaces.get(workspace_id or session_workspace_id or "")
            if workspace_id and workspace is not None and workspace.subject != subject:
                raise PermissionError("Live workspace belongs to a different principal")
            if workspace_id and workspace is None:
                raise LookupError("Live workspace is no longer available")
            if workspace is None:
                workspace = LiveWorkspace(
                    workspace_id=uuid.uuid4().hex,
                    session_key=session_key,
                    subject=subject,
                    scopes=scopes,
                    token_digest=digest,
                    created_at=now,
                    expires_at=expires_at,
                )
                self._workspaces[workspace.workspace_id] = workspace
            self._session_workspaces[session_key] = workspace.workspace_id
            workspace.subject = subject
            workspace.scopes = scopes
            workspace.token_digest = digest
            workspace.expires_at = expires_at
            self._publish_locked(
                workspace,
                "workspace.opened",
                actor="system",
                data={"control": workspace.control},
            )
            return workspace, token

    def authenticate(self, token: str | None) -> LiveWorkspace | None:
        if not token:
            return None
        digest = self._digest(token)
        now = time.time()
        with self._lock:
            self._prune_locked(now)
            for workspace in self._workspaces.values():
                if secrets.compare_digest(workspace.token_digest, digest):
                    return workspace
        return None

    def active_for_session(self, session_key: str) -> LiveWorkspace | None:
        with self._lock:
            self._prune_locked()
            workspace_id = self._session_workspaces.get(session_key)
            return self._workspaces.get(workspace_id or "")

    def by_id(self, workspace_id: str) -> LiveWorkspace | None:
        with self._lock:
            self._prune_locked()
            return self._workspaces.get(workspace_id)

    def _publish_locked(
        self,
        workspace: LiveWorkspace,
        event_type: str,
        *,
        actor: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        workspace.seq += 1
        event = {
            "seq": workspace.seq,
            "ts": time.time(),
            "type": event_type,
            "actor": actor,
            "data": data or {},
        }
        workspace.events.append(event)
        workspace.signal.set()
        return event

    def publish_for_session(
        self,
        session_key: str,
        event_type: str,
        *,
        actor: str = "agent",
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            workspace = self.active_for_session(session_key)
            if workspace is None:
                return None
            return self._publish_locked(workspace, event_type, actor=actor, data=data)

    def publish_workspace(
        self,
        workspace_id: str,
        event_type: str,
        *,
        actor: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            workspace = self._workspaces.get(workspace_id)
            if workspace is None:
                return None
            return self._publish_locked(workspace, event_type, actor=actor, data=data)

    def events_since(
        self,
        workspace: LiveWorkspace,
        after: int,
        limit: int = LIVE_EVENT_BATCH,
    ) -> list[dict[str, Any]]:
        with self._lock:
            return [event for event in workspace.events if int(event["seq"]) > after][:limit]

    async def wait_events(
        self,
        workspace: LiveWorkspace,
        after: int,
        timeout_s: float = LIVE_LONG_POLL_S,
    ) -> list[dict[str, Any]]:
        events = self.events_since(workspace, after)
        if events:
            return events
        workspace.signal.clear()
        events = self.events_since(workspace, after)
        if events:
            return events
        try:
            await asyncio.wait_for(workspace.signal.wait(), timeout=max(0.1, timeout_s))
        except TimeoutError:
            return []
        return self.events_since(workspace, after)

    def set_control(self, workspace: LiveWorkspace, control: str) -> dict[str, Any]:
        if control not in CONTROL_MODES:
            raise ValueError(f"Unsupported control mode: {control}")
        with self._lock:
            previous = workspace.control
            workspace.control = control
            self._publish_locked(
                workspace,
                "control.changed",
                actor="human",
                data={"previous": previous, "control": control},
            )
            return workspace.public_state()

    def require_agent_mutation_allowed(self, session_key: str, tool_name: str) -> None:
        workspace = self.active_for_session(session_key)
        if workspace is None or workspace.control != "human":
            return
        self.publish_for_session(
            session_key,
            "tool.blocked",
            actor="system",
            data={"tool": tool_name, "reason": "human_takeover"},
        )
        raise HumanControlActiveError(
            "The live workspace is in human takeover mode. Read-only tools remain available; "
            "wait for the user to switch control back to Collaborate or Agent before making changes."
        )

    def require_human_mutation_allowed(self, workspace_id: str) -> None:
        workspace = self.by_id(workspace_id)
        if workspace is None:
            raise HumanCollaborationRequiredError("Live workspace is no longer available")
        if workspace.control in {"shared", "human"}:
            return
        raise HumanCollaborationRequiredError(
            "The live workspace is in Observe mode. Switch to Collaborate or Take over before editing."
        )


_MANAGER = LiveWorkspaceManager()


def get_live_workspace_manager() -> LiveWorkspaceManager:
    return _MANAGER


def mcp_session_key(mcp: Any) -> str:
    try:
        context = mcp.get_context()
        request_context = context.request_context
        session = request_context.session
    except (AttributeError, LookupError, ValueError):
        return "direct"

    request = getattr(request_context, "request", None)
    headers = getattr(request, "headers", None)
    if headers is not None:
        session_id = headers.get("mcp-session-id")
        if session_id:
            return f"mcp-http:{session_id}"

    with _SESSION_KEYS_LOCK:
        try:
            key = _SESSION_KEYS.get(session)
        except TypeError:
            key = getattr(session, "_lsm_live_session_key", None)
            if key is None:
                key = uuid.uuid4().hex
                session._lsm_live_session_key = key
            return f"mcp-session:{key}"
        if key is None:
            key = uuid.uuid4().hex
            _SESSION_KEYS[session] = key
    return f"mcp-session:{key}"


def workspace_id_from_claims(claims: dict[str, Any]) -> str | None:
    value = claims.get("live_workspace_id")
    return str(value) if value else None
