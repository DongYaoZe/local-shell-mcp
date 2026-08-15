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
from pathlib import Path
from typing import Any

from .session_runtime import (
    PLAN_EXECUTION_LEASE_S as PLAN_EXECUTION_LEASE_S,
)
from .session_runtime import (
    PLAN_MAX_CONTINUATIONS as PLAN_MAX_CONTINUATIONS,
)
from .session_runtime import (
    get_session_runtime_manager,
)

_LIVE_RESOURCE_PATH = Path(__file__).resolve().parent / "ui_static" / "live-workspace.html"
LIVE_RESOURCE_URI = "ui://local-shell-mcp/live-workspace.html"
LIVE_RESOURCE_TEMPLATE_URI = "ui://local-shell-mcp/live-workspace-{version}.html"


def _versioned_live_resource_uri() -> str:
    try:
        digest = hashlib.sha256(_LIVE_RESOURCE_PATH.read_bytes()).hexdigest()[:16]
    except OSError:
        digest = "unbuilt"
    return LIVE_RESOURCE_TEMPLATE_URI.format(version=digest)


LIVE_RESOURCE_VERSIONED_URI = _versioned_live_resource_uri()
LIVE_RESOURCE_MIME = "text/html;profile=mcp-app"
LIVE_API_PREFIX = "/api/live"
LIVE_TOKEN_TTL_S = 12 * 60 * 60
LIVE_EVENT_LIMIT = 2_000
LIVE_EVENT_BATCH = 300
LIVE_LONG_POLL_S = 25.0
LIVE_RECOVERY_CLAIM_TTL_S = 60.0
_SESSION_KEYS: weakref.WeakKeyDictionary[Any, str] = weakref.WeakKeyDictionary()
_SESSION_KEYS_LOCK = threading.Lock()


@dataclass(slots=True)
class LiveChannel:
    live_id: str
    subject: str
    scopes: tuple[str, ...]
    token_digest: str
    token_value: str = field(repr=False)
    created_at: float
    expires_at: float
    seq: int = 0
    events: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=LIVE_EVENT_LIMIT)
    )
    signal: asyncio.Event = field(default_factory=asyncio.Event)
    logical_session_id: str | None = None

    def public_state(self) -> dict[str, Any]:
        session_manager = get_session_runtime_manager()
        session_state = None
        if self.logical_session_id:
            try:
                session_state = session_manager.get(
                    self.logical_session_id, subject=self.subject
                )
            except (PermissionError, ValueError):
                session_state = None
        return {
            "live_id": self.live_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "seq": self.seq,
            "session_id": self.logical_session_id,
            "session": session_state,
            "plan": session_state.get("plan") if session_state else None,
        }


class LiveChannelManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._channels: dict[str, LiveChannel] = {}
        self._session_channels: dict[str, str] = {}
        self._logical_session_channels: dict[str, str] = {}
        self._recovered_live_ids: dict[str, str] = {}
        self._recovery_claims: dict[str, dict[str, float]] = {}

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
            self._logical_session_channels = {
                session_id: live_id
                for session_id, live_id in self._logical_session_channels.items()
                if live_id not in expired_ids
            }
            self._recovered_live_ids = {
                stale_id: live_id
                for stale_id, live_id in self._recovered_live_ids.items()
                if live_id not in expired_ids
            }
        self._recovery_claims = {
            subject: {
                live_id: deadline
                for live_id, deadline in claims.items()
                if deadline > current and live_id in self._channels
            }
            for subject, claims in self._recovery_claims.items()
        }
        self._recovery_claims = {
            subject: claims for subject, claims in self._recovery_claims.items() if claims
        }

    def open(
        self,
        *,
        session_key: str,
        subject: str,
        scopes: tuple[str, ...],
        parent_expires_at: float | None = None,
        live_id: str | None = None,
        logical_session_id: str | None = None,
    ) -> tuple[LiveChannel, str]:
        now = time.time()
        expires_at = now + LIVE_TOKEN_TTL_S
        if parent_expires_at is not None:
            expires_at = min(expires_at, parent_expires_at)
        with self._lock:
            self._prune_locked(now)
            session_live_id = self._session_channels.get(session_key)
            logical_live_id = (
                self._logical_session_channels.get(logical_session_id)
                if logical_session_id
                else None
            )
            requested_live_id = live_id
            resolved_live_id = self._recovered_live_ids.get(live_id or "", live_id or "")
            channel = self._channels.get(resolved_live_id or "")
            if channel is None:
                channel = self._channels.get(logical_live_id or "")
            if channel is None:
                channel = self._channels.get(session_live_id or "")
            if (
                channel is not None
                and logical_session_id
                and channel.logical_session_id not in {None, logical_session_id}
            ):
                channel = self._channels.get(logical_live_id or "")
            if channel is not None and channel.subject != subject:
                if live_id:
                    raise PermissionError("Live workspace belongs to a different principal")
                channel = None
            if channel is None:
                token = secrets.token_urlsafe(32)
                digest = self._digest(token)
                channel = LiveChannel(
                    live_id=uuid.uuid4().hex,
                    subject=subject,
                    scopes=scopes,
                    token_digest=digest,
                    token_value=token,
                    created_at=now,
                    expires_at=expires_at,
                    logical_session_id=logical_session_id,
                )
                self._channels[channel.live_id] = channel
                if requested_live_id:
                    self._recovered_live_ids[requested_live_id] = channel.live_id
                    self._recovery_claims.setdefault(subject, {})[channel.live_id] = (
                        now + LIVE_RECOVERY_CLAIM_TTL_S
                    )
            elif live_id is not None:
                # App-side reattachment must not rotate the credential or several
                # cached/reconnecting views would continually invalidate each other.
                token = channel.token_value
            else:
                # An explicit user/model open is a new authorization boundary.
                token = secrets.token_urlsafe(32)
                channel.token_value = token
                channel.token_digest = self._digest(token)
            self._session_channels[session_key] = channel.live_id
            if logical_session_id:
                previous_session_id = channel.logical_session_id
                if (
                    previous_session_id
                    and previous_session_id != logical_session_id
                    and self._logical_session_channels.get(previous_session_id) == channel.live_id
                ):
                    self._logical_session_channels.pop(previous_session_id, None)
                channel.logical_session_id = logical_session_id
                self._logical_session_channels[logical_session_id] = channel.live_id
            channel.subject = subject
            channel.scopes = scopes
            channel.expires_at = expires_at
            self._publish_locked(
                channel,
                "channel.opened",
                actor="system",
                data={},
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

    def bind_logical_session(
        self, session_key: str, logical_session_id: str, subject: str
    ) -> LiveChannel | None:
        with self._lock:
            self._prune_locked()
            live_id = self._session_channels.get(session_key)
            if live_id is None:
                live_id = self._logical_session_channels.get(logical_session_id)
            channel = self._channels.get(live_id or "")
            if channel is None:
                return None
            if channel.subject != subject:
                if self._session_channels.get(session_key) == channel.live_id:
                    self._session_channels.pop(session_key, None)
                return None
            previous_session_id = channel.logical_session_id
            if (
                previous_session_id
                and previous_session_id != logical_session_id
                and any(
                    key != session_key and mapped_live_id == channel.live_id
                    for key, mapped_live_id in self._session_channels.items()
                )
            ):
                # This transport is switching tasks, but another transport still
                # owns the existing task view. Do not move their shared channel.
                self._session_channels.pop(session_key, None)
                target_live_id = self._logical_session_channels.get(logical_session_id)
                channel = self._channels.get(target_live_id or "")
                if channel is None or channel.subject != subject:
                    return None
            self._session_channels[session_key] = channel.live_id
            previous_session_id = channel.logical_session_id
            if (
                previous_session_id
                and previous_session_id != logical_session_id
                and self._logical_session_channels.get(previous_session_id) == channel.live_id
            ):
                self._logical_session_channels.pop(previous_session_id, None)
            channel.logical_session_id = logical_session_id
            self._logical_session_channels[logical_session_id] = channel.live_id
            self._publish_locked(
                channel,
                "session.attached",
                actor="system",
                data={"session_id": logical_session_id},
            )
            return channel

    def detach_logical_session(self, logical_session_id: str) -> list[LiveChannel]:
        with self._lock:
            self._prune_locked()
            self._logical_session_channels.pop(logical_session_id, None)
            detached: list[LiveChannel] = []
            for channel in self._channels.values():
                if channel.logical_session_id != logical_session_id:
                    continue
                channel.logical_session_id = None
                detached.append(channel)
                self._publish_locked(
                    channel,
                    "session.detached",
                    actor="system",
                    data={"session_id": logical_session_id},
                )
            return detached

    def claim_recovery_session(self, session_key: str, subject: str) -> LiveChannel | None:
        """Attach one fresh model MCP session after a backend restart recovery."""
        with self._lock:
            self._prune_locked()
            existing = self.active_for_session(session_key)
            if existing is not None:
                return existing
            claims = self._recovery_claims.get(subject)
            if not claims or len(claims) != 1:
                # Multiple recovered chats for the same OAuth subject cannot be
                # correlated safely from a fresh model MCP session alone. Keep
                # every claim rather than guessing and leaking one chat's live
                # activity into another.
                return None
            live_id, deadline = next(iter(claims.items()))
            if deadline <= time.time():
                return None
            channel = self._channels.get(live_id)
            if channel is None:
                return None
            self._recovery_claims.pop(subject, None)
            self._session_channels[session_key] = channel.live_id
            return channel

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
        now = time.time()
        event = {
            "seq": channel.seq,
            "ts": now,
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
