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
PLAN_EXECUTION_LEASE_S = 15 * 60
PLAN_MAX_CONTINUATIONS = 10
PLAN_CONTINUATION_PENDING_TTL_S = 5 * 60
PLAN_MAX_STEPS = 100
PLAN_STEP_STATUSES = frozenset({"pending", "active", "completed", "skipped"})
_SESSION_KEYS: weakref.WeakKeyDictionary[Any, str] = weakref.WeakKeyDictionary()
_SESSION_KEYS_LOCK = threading.Lock()


@dataclass(slots=True)
class PlanStep:
    id: str
    text: str
    status: str = "pending"
    note: str | None = None

    def public_state(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id, "text": self.text, "status": self.status}
        if self.note:
            data["note"] = self.note
        return data


@dataclass(slots=True)
class PlanState:
    plan_id: str
    objective: str
    steps: list[PlanStep]
    created_at: float
    updated_at: float
    status: str = "active"
    revision: int = 1
    note: str | None = None
    continuation_count: int = 0
    continuation_pending: bool = False
    continuation_pending_since: float | None = None
    last_continuation_at: float | None = None
    last_agent_activity: float = 0.0

    def has_unfinished_steps(self) -> bool:
        return any(step.status in {"pending", "active"} for step in self.steps)

    def public_state(self, now: float | None = None) -> dict[str, Any]:
        current = time.time() if now is None else now
        due_at = self.last_agent_activity + PLAN_EXECUTION_LEASE_S
        return {
            "plan_id": self.plan_id,
            "objective": self.objective,
            "status": self.status,
            "steps": [step.public_state() for step in self.steps],
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "note": self.note,
            "continuation_count": self.continuation_count,
            "continuation_pending": self.continuation_pending,
            "last_continuation_at": self.last_continuation_at,
            "last_agent_activity": self.last_agent_activity,
            "execution_lease_s": PLAN_EXECUTION_LEASE_S,
            "continuation_due_at": due_at,
            "continuation_due": (
                self.status == "active"
                and self.has_unfinished_steps()
                and not self.continuation_pending
                and self.continuation_count < PLAN_MAX_CONTINUATIONS
                and current >= due_at
            ),
            "max_continuations": PLAN_MAX_CONTINUATIONS,
            "auto_continue_exhausted": self.continuation_count >= PLAN_MAX_CONTINUATIONS,
        }


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
    plan: PlanState | None = None

    def public_state(self) -> dict[str, Any]:
        return {
            "live_id": self.live_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "seq": self.seq,
            "plan": self.plan.public_state() if self.plan else None,
        }


class LiveChannelManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._channels: dict[str, LiveChannel] = {}
        self._session_channels: dict[str, str] = {}
        self._recovered_live_ids: dict[str, str] = {}
        self._recovery_claims: dict[str, tuple[str, float]] = {}

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
            self._recovered_live_ids = {
                stale_id: live_id
                for stale_id, live_id in self._recovered_live_ids.items()
                if live_id not in expired_ids
            }
        self._recovery_claims = {
            subject: (live_id, deadline)
            for subject, (live_id, deadline) in self._recovery_claims.items()
            if deadline > current and live_id in self._channels
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
        with self._lock:
            self._prune_locked(now)
            session_live_id = self._session_channels.get(session_key)
            requested_live_id = live_id
            resolved_live_id = self._recovered_live_ids.get(live_id or "", live_id or "")
            channel = self._channels.get(resolved_live_id or session_live_id or "")
            if live_id and channel is not None and channel.subject != subject:
                raise PermissionError("Live workspace belongs to a different principal")
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
                )
                self._channels[channel.live_id] = channel
                if requested_live_id:
                    self._recovered_live_ids[requested_live_id] = channel.live_id
                    self._recovery_claims[subject] = (
                        channel.live_id,
                        now + LIVE_RECOVERY_CLAIM_TTL_S,
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

    def claim_recovery_session(self, session_key: str, subject: str) -> LiveChannel | None:
        """Attach one fresh model MCP session after a backend restart recovery."""
        with self._lock:
            self._prune_locked()
            existing = self.active_for_session(session_key)
            if existing is not None:
                return existing
            claim = self._recovery_claims.pop(subject, None)
            if claim is None:
                return None
            live_id, deadline = claim
            if deadline <= time.time():
                return None
            channel = self._channels.get(live_id)
            if channel is None:
                return None
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
        if actor == "agent" and channel.plan is not None and channel.plan.status == "active":
            channel.plan.last_agent_activity = now
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

    @staticmethod
    def _normalize_plan_steps(steps: list[dict[str, Any]]) -> list[PlanStep]:
        if not steps:
            raise ValueError("A plan requires at least one step")
        if len(steps) > PLAN_MAX_STEPS:
            raise ValueError(f"A plan may contain at most {PLAN_MAX_STEPS} steps")
        normalized: list[PlanStep] = []
        seen: set[str] = set()
        for index, raw in enumerate(steps):
            step_id = str(raw.get("id") or f"step-{index + 1}").strip()
            text = str(raw.get("text") or raw.get("content") or raw.get("title") or "").strip()
            status = str(raw.get("status") or "pending").strip().lower()
            note = str(raw.get("note") or "").strip() or None
            if not step_id or step_id in seen:
                raise ValueError(f"Plan step ids must be unique; invalid id at index {index}")
            if not text:
                raise ValueError(f"Plan step {step_id!r} has no text")
            if status not in PLAN_STEP_STATUSES:
                raise ValueError(f"Unsupported plan step status: {status}")
            seen.add(step_id)
            normalized.append(PlanStep(step_id, text, status, note))
        active = [step for step in normalized if step.status == "active"]
        if len(active) > 1:
            raise ValueError("A plan may have at most one active step")
        if not active:
            next_step = next((step for step in normalized if step.status == "pending"), None)
            if next_step is not None:
                next_step.status = "active"
        return normalized

    @staticmethod
    def _promote_next_step(plan: PlanState) -> None:
        if any(step.status == "active" for step in plan.steps):
            return
        next_step = next((step for step in plan.steps if step.status == "pending"), None)
        if next_step is not None:
            next_step.status = "active"

    def manage_plan(
        self,
        session_key: str,
        *,
        action: str,
        objective: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        step_id: str | None = None,
        status: str | None = None,
        text: str | None = None,
        note: str | None = None,
        actor: str = "agent",
    ) -> dict[str, Any]:
        with self._lock:
            channel = self.active_for_session(session_key)
            return self._manage_plan_locked(
                channel,
                action=action,
                objective=objective,
                steps=steps,
                step_id=step_id,
                status=status,
                text=text,
                note=note,
                actor=actor,
            )

    def manage_channel_plan(
        self,
        channel: LiveChannel,
        *,
        action: str,
        note: str | None = None,
        actor: str = "human",
    ) -> dict[str, Any]:
        with self._lock:
            return self._manage_plan_locked(channel, action=action, note=note, actor=actor)

    def _manage_plan_locked(
        self,
        channel: LiveChannel | None,
        *,
        action: str,
        objective: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        step_id: str | None = None,
        status: str | None = None,
        text: str | None = None,
        note: str | None = None,
        actor: str,
    ) -> dict[str, Any]:
        normalized_action = action.strip().lower()
        if normalized_action == "get":
            return {
                "goal_mode": bool(channel and channel.plan and channel.plan.status in {"active", "blocked"}),
                "plan": channel.plan.public_state() if channel and channel.plan else None,
            }
        if channel is None:
            raise ValueError(
                "Goal mode requires an active Live Workspace. Call open_live_workspace first, then retry plan_manage."
            )
        now = time.time()
        plan = channel.plan
        if normalized_action == "start":
            if plan is not None and plan.status in {"active", "blocked"}:
                raise ValueError("A plan is already active; finish or cancel it before starting another")
            objective_text = str(objective or "").strip()
            if not objective_text:
                raise ValueError("objective is required for action=start")
            normalized_steps = self._normalize_plan_steps(list(steps or []))
            plan = PlanState(
                plan_id=uuid.uuid4().hex,
                objective=objective_text,
                steps=normalized_steps,
                created_at=now,
                updated_at=now,
                last_agent_activity=now,
            )
            channel.plan = plan
            self._publish_locked(
                channel,
                "plan.started",
                actor=actor,
                data={"plan_id": plan.plan_id, "objective": plan.objective},
            )
        else:
            if plan is None:
                raise ValueError("No plan exists in this Live Workspace")
            if normalized_action == "update":
                if plan.status not in {"active", "blocked"}:
                    raise ValueError(f"Cannot update a {plan.status} plan")
                changed = False
                if objective is not None:
                    objective_text = objective.strip()
                    if not objective_text:
                        raise ValueError("objective cannot be empty")
                    plan.objective = objective_text
                    changed = True
                if steps is not None:
                    plan.steps = self._normalize_plan_steps(list(steps))
                    changed = True
                if step_id is not None:
                    target = next((step for step in plan.steps if step.id == step_id), None)
                    if target is None:
                        raise ValueError(f"Unknown plan step: {step_id}")
                    if status is not None:
                        normalized_status = status.strip().lower()
                        if normalized_status not in PLAN_STEP_STATUSES:
                            raise ValueError(f"Unsupported plan step status: {normalized_status}")
                        if normalized_status == "active":
                            for item in plan.steps:
                                if item is not target and item.status == "active":
                                    item.status = "pending"
                        target.status = normalized_status
                        changed = True
                    if text is not None:
                        normalized_text = text.strip()
                        if not normalized_text:
                            raise ValueError("step text cannot be empty")
                        target.text = normalized_text
                        changed = True
                    if note is not None:
                        target.note = note.strip() or None
                        changed = True
                elif status is not None or text is not None:
                    raise ValueError("step_id is required when updating step status or text")
                if note is not None and step_id is None:
                    plan.note = note.strip() or None
                    changed = True
                if not changed:
                    raise ValueError("action=update requires objective, steps, step_id, or note")
                self._promote_next_step(plan)
                plan.revision += 1
                plan.updated_at = now
                self._publish_locked(
                    channel,
                    "plan.updated",
                    actor=actor,
                    data={"plan_id": plan.plan_id, "revision": plan.revision},
                )
            elif normalized_action == "block":
                if plan.status != "active":
                    raise ValueError(f"Cannot block a {plan.status} plan")
                reason = str(note or "").strip()
                if not reason:
                    raise ValueError("note is required for action=block")
                plan.status = "blocked"
                plan.note = reason
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                self._publish_locked(channel, "plan.blocked", actor=actor, data={"plan_id": plan.plan_id, "reason": reason})
            elif normalized_action == "resume":
                if plan.status != "blocked":
                    raise ValueError("Only a blocked plan can be resumed")
                plan.status = "active"
                plan.note = None
                plan.revision += 1
                plan.updated_at = now
                plan.last_agent_activity = now
                self._publish_locked(channel, "plan.resumed", actor=actor, data={"plan_id": plan.plan_id})
            elif normalized_action == "finish":
                if plan.status not in {"active", "blocked"}:
                    raise ValueError(f"Cannot finish a {plan.status} plan")
                unfinished = [step.id for step in plan.steps if step.status in {"pending", "active"}]
                if unfinished:
                    raise ValueError("Cannot finish plan while unfinished steps remain: " + ", ".join(unfinished))
                plan.status = "completed"
                plan.note = str(note or "").strip() or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                self._publish_locked(channel, "plan.completed", actor=actor, data={"plan_id": plan.plan_id})
            elif normalized_action == "cancel":
                if plan.status in {"completed", "cancelled"}:
                    raise ValueError(f"Plan is already {plan.status}")
                plan.status = "cancelled"
                plan.note = str(note or "").strip() or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                self._publish_locked(channel, "plan.cancelled", actor=actor, data={"plan_id": plan.plan_id})
            else:
                raise ValueError("action must be one of: start, get, update, block, resume, finish, cancel")
        return {"goal_mode": plan.status in {"active", "blocked"}, "plan": plan.public_state(now)}

    def claim_plan_continuation(self, channel: LiveChannel) -> dict[str, Any] | None:
        with self._lock:
            plan = channel.plan
            if plan is None or plan.status != "active" or not plan.has_unfinished_steps():
                return None
            now = time.time()
            if plan.continuation_pending:
                pending_since = plan.continuation_pending_since or now
                if now - pending_since < PLAN_CONTINUATION_PENDING_TTL_S:
                    return None
                plan.continuation_pending = False
                plan.continuation_pending_since = None
            if plan.continuation_count >= PLAN_MAX_CONTINUATIONS:
                return None
            if now < plan.last_agent_activity + PLAN_EXECUTION_LEASE_S:
                return None
            plan.continuation_pending = True
            plan.continuation_pending_since = now
            plan.updated_at = now
            recent = list(channel.events)[-20:]
            self._publish_locked(
                channel,
                "plan.continuation_requested",
                actor="system",
                data={"plan_id": plan.plan_id, "attempt": plan.continuation_count + 1},
            )
            return {
                "plan": plan.public_state(now),
                "recent_events": recent,
                "continuation_count": plan.continuation_count + 1,
            }

    def report_plan_continuation(
        self, channel: LiveChannel, *, accepted: bool, error: str | None = None
    ) -> dict[str, Any]:
        with self._lock:
            plan = channel.plan
            if plan is None:
                raise ValueError("No plan exists in this Live Workspace")
            if not plan.continuation_pending:
                raise ValueError("No plan continuation is pending")
            now = time.time()
            plan.continuation_pending = False
            plan.continuation_pending_since = None
            if accepted:
                plan.continuation_count += 1
                plan.last_continuation_at = now
                plan.last_agent_activity = now
            plan.updated_at = now
            self._publish_locked(
                channel,
                "plan.continuation_sent" if accepted else "plan.continuation_failed",
                actor="system",
                data={
                    "plan_id": plan.plan_id,
                    "count": plan.continuation_count,
                    **({"error": error[:500]} if error else {}),
                },
            )
            return plan.public_state(now)

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
