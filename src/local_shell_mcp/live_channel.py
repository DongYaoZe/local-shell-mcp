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
class LiveChannel:
    live_id: str
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
            "live_id": self.live_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "control": self.control,
            "seq": self.seq,
        }


class LiveChannelManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._channels: dict[str, LiveChannel] = {}
        self._session_channels: dict[str, str] = {}

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _prune_locked(self, now: float | None = None) -> None:
        current = time.time() if now is None else now
        expired = [
            live_id
            for live_id, channel in self._channels.items()
            if channel.expires_at <= current
        ]
        for live_id in expired:
            self._channels.pop(live_id, None)
        if expired:
            expired_ids = set(expired)
            self._session_channels = {
                session_key: live_id
                for session_key, live_id in self._session_channels.items()
                if live_id not in expired_ids
            }

    def open(
        self,
        *,
        session_key: str,
        subject: str,
        scopes: tuple[str, ...],
        parent_expires_at: float | None = None,
        live_id: str | None = None,
    ) -> tuple[LiveChannel, str]:
        now = time.time()
        expires_at = now + LIVE_TOKEN_TTL_S
        if parent_expires_at is not None:
            expires_at = min(expires_at, parent_expires_at)
        token = secrets.token_urlsafe(32)
        digest = self._digest(token)
        with self._lock:
            self._prune_locked(now)
            session_live_id = self._session_channels.get(session_key)
            channel = self._channels.get(live_id or session_live_id or "")
            if live_id and channel is not None and channel.subject != subject:
                raise PermissionError("Live workspace belongs to a different principal")
            if live_id and channel is None:
                raise LookupError("Live workspace is no longer available")
            if channel is None:
                channel = LiveChannel(
                    live_id=uuid.uuid4().hex,
                    subject=subject,
                    scopes=scopes,
                    token_digest=digest,
                    created_at=now,
                    expires_at=expires_at,
                )
                self._channels[channel.live_id] = channel
            self._session_channels[session_key] = channel.live_id
            channel.subject = subject
            channel.scopes = scopes
            channel.token_digest = digest
            channel.expires_at = expires_at
            self._publish_locked(
                channel,
                "channel.opened",
                actor="system",
                data={"control": channel.control},
            )
            return channel, token

    def authenticate(self, token: str | None) -> LiveChannel | None:
        if not token:
            return None
        digest = self._digest(token)
        now = time.time()
        with self._lock:
            self._prune_locked(now)
            for channel in self._channels.values():
                if secrets.compare_digest(channel.token_digest, digest):
                    return channel
        return None

    def active_for_session(self, session_key: str) -> LiveChannel | None:
        with self._lock:
            self._prune_locked()
            live_id = self._session_channels.get(session_key)
            return self._channels.get(live_id or "")

    def by_id(self, live_id: str) -> LiveChannel | None:
        with self._lock:
            self._prune_locked()
            return self._channels.get(live_id)

    def _publish_locked(
        self,
        channel: LiveChannel,
        event_type: str,
        *,
        actor: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        channel.seq += 1
        event = {
            "seq": channel.seq,
            "ts": time.time(),
            "type": event_type,
            "actor": actor,
            "data": data or {},
        }
        channel.events.append(event)
        channel.signal.set()
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
            channel = self.active_for_session(session_key)
            if channel is None:
                return None
            return self._publish_locked(channel, event_type, actor=actor, data=data)

    def publish_channel(
        self,
        live_id: str,
        event_type: str,
        *,
        actor: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            channel = self._channels.get(live_id)
            if channel is None:
                return None
            return self._publish_locked(channel, event_type, actor=actor, data=data)

    def events_since(
        self,
        channel: LiveChannel,
        after: int,
        limit: int = LIVE_EVENT_BATCH,
    ) -> list[dict[str, Any]]:
        with self._lock:
            return [event for event in channel.events if int(event["seq"]) > after][:limit]

    async def wait_events(
        self,
        channel: LiveChannel,
        after: int,
        timeout_s: float = LIVE_LONG_POLL_S,
    ) -> list[dict[str, Any]]:
        events = self.events_since(channel, after)
        if events:
            return events
        channel.signal.clear()
        events = self.events_since(channel, after)
        if events:
            return events
        try:
            await asyncio.wait_for(channel.signal.wait(), timeout=max(0.1, timeout_s))
        except TimeoutError:
            return []
        return self.events_since(channel, after)

    def set_control(self, channel: LiveChannel, control: str) -> dict[str, Any]:
        if control not in CONTROL_MODES:
            raise ValueError(f"Unsupported control mode: {control}")
        with self._lock:
            previous = channel.control
            channel.control = control
            self._publish_locked(
                channel,
                "control.changed",
                actor="human",
                data={"previous": previous, "control": control},
            )
            return channel.public_state()

    def require_agent_mutation_allowed(self, session_key: str, tool_name: str) -> None:
        channel = self.active_for_session(session_key)
        if channel is None or channel.control != "human":
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

    def require_human_mutation_allowed(self, live_id: str) -> None:
        channel = self.by_id(live_id)
        if channel is None:
            raise HumanCollaborationRequiredError("Live workspace is no longer available")
        if channel.control in {"shared", "human"}:
            return
        raise HumanCollaborationRequiredError(
            "The live workspace is in Observe mode. Switch to Collaborate or Take over before editing."
        )


_MANAGER = LiveChannelManager()


def get_live_channel_manager() -> LiveChannelManager:
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


def live_id_from_claims(claims: dict[str, Any]) -> str | None:
    value = claims.get("live_id")
    return str(value) if value else None
