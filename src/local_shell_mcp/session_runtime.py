from __future__ import annotations

import contextlib
import copy
import json
import secrets
import threading
import time
import uuid
from collections import deque
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .auth import current_principal
from .settings import get_settings
from .state_store import FileStateStore, get_state_store

PLAN_EXECUTION_LEASE_S = 15 * 60
PLAN_MAX_CONTINUATIONS = 10
PLAN_CONTINUATION_PENDING_TTL_S = 5 * 60
PLAN_CONTINUATION_FAILURE_BACKOFF_S = 5 * 60
PLAN_MAX_STEPS = 100
PLAN_OBJECTIVE_LIMIT = 4_000
PLAN_STEP_ID_LIMIT = 128
PLAN_STEP_TEXT_LIMIT = 2_000
PLAN_NOTE_LIMIT = 2_000
PLAN_STEP_STATUSES = frozenset({"pending", "active", "completed", "skipped"})
SESSION_ACTIVITY_LIMIT = 200
SESSION_IN_FLIGHT_LEASE_S = 2 * 60 * 60
SESSION_RUN_HISTORY_LIMIT = 100
SESSION_HISTORY_LIMIT_PER_PRINCIPAL = 100
SESSION_REPORT_LIST_LIMIT = 50
SESSION_TEXT_LIMIT = 20_000
SESSION_LIST_LIMIT = 100
SESSION_LIST_TEXT_LIMIT = 500


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
    continuation_claim_id: str | None = None
    last_continuation_at: float | None = None
    continuation_retry_after: float | None = None
    last_agent_activity: float = 0.0

    def has_unfinished_steps(self) -> bool:
        return any(step.status in {"pending", "active"} for step in self.steps)

    def public_state(
        self, now: float | None = None, *, in_flight_calls: int = 0
    ) -> dict[str, Any]:
        current = time.time() if now is None else now
        due_at = self.last_agent_activity + PLAN_EXECUTION_LEASE_S
        retry_due = self.continuation_retry_after is None or current >= self.continuation_retry_after
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
            "continuation_claim_id": self.continuation_claim_id,
            "last_continuation_at": self.last_continuation_at,
            "continuation_retry_after": self.continuation_retry_after,
            "last_agent_activity": self.last_agent_activity,
            "in_flight_calls": in_flight_calls,
            "execution_lease_s": PLAN_EXECUTION_LEASE_S,
            "continuation_due_at": due_at,
            "continuation_due": (
                self.status == "active"
                and not self.continuation_pending
                and in_flight_calls == 0
                and self.continuation_count < PLAN_MAX_CONTINUATIONS
                and current >= due_at
                and retry_due
            ),
            "max_continuations": PLAN_MAX_CONTINUATIONS,
            "auto_continue_exhausted": self.continuation_count >= PLAN_MAX_CONTINUATIONS,
        }


@dataclass(slots=True)
class AgentRun:
    run_id: str
    session_key: str
    created_at: float
    updated_at: float
    status: str = "active"

    def public_state(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
        }


@dataclass(slots=True)
class ProgressState:
    summary: str | None = None
    findings: list[str] = field(default_factory=list)
    next: str | None = None
    blockers: list[str] = field(default_factory=list)
    updated_at: float | None = None

    def public_state(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "findings": list(self.findings),
            "next": self.next,
            "blockers": list(self.blockers),
            "updated_at": self.updated_at,
        }

    def list_state(self) -> dict[str, Any]:
        def compact(value: str | None) -> str | None:
            return None if value is None else value[:SESSION_LIST_TEXT_LIMIT]

        return {
            "summary": compact(self.summary),
            "next": compact(self.next),
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class LogicalSession:
    session_id: str
    subject: str
    created_at: float
    updated_at: float
    status: str = "active"
    label: str | None = None
    objective: str | None = None
    active_run_id: str | None = None
    runs: list[AgentRun] = field(default_factory=list)
    progress: ProgressState = field(default_factory=ProgressState)
    plan: PlanState | None = None
    in_flight_calls: dict[str, dict[str, Any]] = field(default_factory=dict)
    activity_seq: int = 0
    activity: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=SESSION_ACTIVITY_LIMIT)
    )

    def active_run(self) -> AgentRun | None:
        if not self.active_run_id:
            return None
        return next((run for run in self.runs if run.run_id == self.active_run_id), None)

    def public_state(
        self, *, recent_activity: int = 30, in_flight_calls: int = 0
    ) -> dict[str, Any]:
        active = self.active_run()
        return {
            "session_id": self.session_id,
            "label": self.label,
            "objective": self.objective,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active_run": active.public_state() if active else None,
            "runs": [run.public_state() for run in self.runs[-20:]],
            "progress": self.progress.public_state(),
            "plan": (
                self.plan.public_state(in_flight_calls=in_flight_calls)
                if self.plan
                else None
            ),
            "recent_activity": (
                list(self.activity)[-min(recent_activity, 100) :]
                if recent_activity > 0
                else []
            ),
        }


class SessionRuntimeManager:
    """Durable logical task sessions, independent of machines and workdirs."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self._lock = threading.RLock()
        self._state_dir_override = state_dir
        self._loaded_storage: tuple[str, ...] | None = None
        self._sessions: dict[str, LogicalSession] = {}
        self._attachments: dict[str, tuple[str, str]] = {}

    def _state_store(self):  # noqa: ANN202
        if self._state_dir_override is not None:
            return FileStateStore(Path(self._state_dir_override))
        return get_state_store()

    def _storage_signature(self) -> tuple[str, ...]:
        if self._state_dir_override is not None:
            return ("override", str(Path(self._state_dir_override).resolve()))
        settings = get_settings()
        return (
            settings.state_backend,
            settings.state_backend_url or "",
            settings.state_backend_prefix,
            str(settings.state_dir),
        )

    def _ensure_loaded_locked(self) -> None:
        signature = self._storage_signature()
        if self._loaded_storage == signature:
            return
        store = self._state_store()
        loaded_sessions: dict[str, LogicalSession] = {}
        for key in store.list_keys("sessions/"):
            if not key.endswith(".json"):
                continue
            try:
                raw = store.read_bytes(key)
                if raw is None:
                    continue
                payload = json.loads(raw.decode("utf-8"))
                session = self._session_from_payload(payload)
            except (
                OSError,
                UnicodeDecodeError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):
                continue
            loaded_sessions[session.session_id] = session
        self._sessions = loaded_sessions
        self._attachments.clear()
        self._loaded_storage = signature

    def _uses_shared_state_backend(self) -> bool:
        return self._state_dir_override is None and get_settings().state_backend == "redis"

    def _load_session_from_store_locked(self, session_id: str) -> LogicalSession | None:
        raw = self._state_store().read_bytes(f"sessions/{session_id}.json")
        if raw is None:
            return None
        try:
            payload = json.loads(raw.decode("utf-8"))
            return self._session_from_payload(payload)
        except (
            OSError,
            UnicodeDecodeError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            return None

    def _refresh_session_locked(self, session_id: str) -> None:
        if not self._uses_shared_state_backend():
            return
        refreshed = self._load_session_from_store_locked(session_id)
        if refreshed is None:
            self._sessions.pop(session_id, None)
        else:
            self._restore_local_run_owners_locked(refreshed)
            self._sessions[session_id] = refreshed

    def _refresh_all_sessions_locked(self) -> None:
        if not self._uses_shared_state_backend():
            return
        refreshed: dict[str, LogicalSession] = {}
        store = self._state_store()
        for key in store.list_keys("sessions/"):
            if not key.endswith(".json"):
                continue
            session_id = key.removeprefix("sessions/").removesuffix(".json")
            session = self._load_session_from_store_locked(session_id)
            if session is not None:
                self._restore_local_run_owners_locked(session)
                refreshed[session.session_id] = session
        self._sessions = refreshed

    @contextlib.contextmanager
    def _shared_session_locks_locked(self, session_ids: list[str]) -> Iterator[None]:
        normalized = sorted({str(item) for item in session_ids if item})
        if not normalized or not self._uses_shared_state_backend():
            yield
            return
        store = self._state_store()
        with contextlib.ExitStack() as stack:
            for session_id in normalized:
                stack.enter_context(store.lock(f"sessions/{session_id}"))
            yield

    def _restore_local_run_owners_locked(self, session: LogicalSession) -> None:
        for session_key, (session_id, run_id) in self._attachments.items():
            if session_id != session.session_id:
                continue
            run = next((item for item in session.runs if item.run_id == run_id), None)
            if run is not None:
                run.session_key = session_key

    @staticmethod
    def _bounded_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        return normalized[:SESSION_TEXT_LIMIT]

    @classmethod
    def _bounded_list(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized = [
            item
            for item in (cls._bounded_text(str(value)) for value in values)
            if item is not None
        ]
        return normalized[:SESSION_REPORT_LIST_LIMIT]

    @staticmethod
    def _plan_to_payload(plan: PlanState | None) -> dict[str, Any] | None:
        if plan is None:
            return None
        return {
            "plan_id": plan.plan_id,
            "objective": plan.objective,
            "steps": [asdict(step) for step in plan.steps],
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "status": plan.status,
            "revision": plan.revision,
            "note": plan.note,
            "continuation_count": plan.continuation_count,
            "continuation_pending": plan.continuation_pending,
            "continuation_pending_since": plan.continuation_pending_since,
            "continuation_claim_id": plan.continuation_claim_id,
            "last_continuation_at": plan.last_continuation_at,
            "continuation_retry_after": plan.continuation_retry_after,
            "last_agent_activity": plan.last_agent_activity,
        }

    @staticmethod
    def _bounded_plan_text(value: Any, limit: int) -> str:
        return str(value or "").strip()[:limit]

    @classmethod
    def _plan_from_payload(cls, payload: Any) -> PlanState | None:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise ValueError("invalid plan state")
        steps_payload = payload.get("steps")
        if not isinstance(steps_payload, list):
            raise ValueError("invalid plan steps")
        return PlanState(
            plan_id=str(payload["plan_id"]),
            objective=cls._bounded_plan_text(payload["objective"], PLAN_OBJECTIVE_LIMIT),
            steps=[
                PlanStep(
                    id=cls._bounded_plan_text(step["id"], PLAN_STEP_ID_LIMIT),
                    text=cls._bounded_plan_text(step["text"], PLAN_STEP_TEXT_LIMIT),
                    status=str(step.get("status") or "pending"),
                    note=(
                        None
                        if step.get("note") is None
                        else cls._bounded_plan_text(step["note"], PLAN_NOTE_LIMIT) or None
                    ),
                )
                for step in steps_payload
                if isinstance(step, dict)
            ],
            created_at=float(payload["created_at"]),
            updated_at=float(payload["updated_at"]),
            status=str(payload.get("status") or "active"),
            revision=int(payload.get("revision") or 1),
            note=(
                None
                if payload.get("note") is None
                else cls._bounded_plan_text(payload["note"], PLAN_NOTE_LIMIT) or None
            ),
            continuation_count=int(payload.get("continuation_count") or 0),
            continuation_pending=bool(payload.get("continuation_pending")),
            continuation_pending_since=(
                None
                if payload.get("continuation_pending_since") is None
                else float(payload["continuation_pending_since"])
            ),
            continuation_claim_id=(
                None
                if payload.get("continuation_claim_id") is None
                else str(payload["continuation_claim_id"])
            ),
            last_continuation_at=(
                None
                if payload.get("last_continuation_at") is None
                else float(payload["last_continuation_at"])
            ),
            continuation_retry_after=(
                None
                if payload.get("continuation_retry_after") is None
                else float(payload["continuation_retry_after"])
            ),
            last_agent_activity=float(payload.get("last_agent_activity") or 0.0),
        )

    @staticmethod
    def _bounded_run_history(
        runs: list[AgentRun], active_run_id: str | None
    ) -> list[AgentRun]:
        if len(runs) <= SESSION_RUN_HISTORY_LIMIT:
            return runs
        recent = runs[-SESSION_RUN_HISTORY_LIMIT:]
        if active_run_id and all(run.run_id != active_run_id for run in recent):
            active = next((run for run in reversed(runs) if run.run_id == active_run_id), None)
            if active is not None:
                recent = [active, *recent[-(SESSION_RUN_HISTORY_LIMIT - 1) :]]
        return recent

    @classmethod
    def _session_from_payload(cls, payload: Any) -> LogicalSession:
        if not isinstance(payload, dict):
            raise ValueError("session metadata must be an object")
        progress_payload = payload.get("progress") or {}
        if not isinstance(progress_payload, dict):
            raise ValueError("invalid progress state")
        runs_payload = payload.get("runs") or []
        if not isinstance(runs_payload, list):
            raise ValueError("invalid run state")
        activity_payload = payload.get("activity") or []
        if not isinstance(activity_payload, list):
            raise ValueError("invalid activity state")
        in_flight_payload = payload.get("in_flight_calls") or {}
        if not isinstance(in_flight_payload, dict):
            raise ValueError("invalid in-flight tool state")
        active_run_id = (
            None if payload.get("active_run_id") is None else str(payload["active_run_id"])
        )
        runs = cls._bounded_run_history(
            [
                AgentRun(
                    run_id=str(run["run_id"]),
                    session_key=str(run.get("session_key") or "persisted"),
                    created_at=float(run["created_at"]),
                    updated_at=float(run["updated_at"]),
                    status=str(run.get("status") or "active"),
                )
                for run in runs_payload
                if isinstance(run, dict)
            ],
            active_run_id,
        )
        return LogicalSession(
            session_id=str(payload["session_id"]),
            subject=str(payload["subject"]),
            created_at=float(payload["created_at"]),
            updated_at=float(payload["updated_at"]),
            status=str(payload.get("status") or "active"),
            label=cls._bounded_text(payload.get("label")),
            objective=cls._bounded_text(payload.get("objective")),
            active_run_id=active_run_id,
            runs=runs,
            progress=ProgressState(
                summary=cls._bounded_text(progress_payload.get("summary")),
                findings=cls._bounded_list(progress_payload.get("findings")) or [],
                next=cls._bounded_text(progress_payload.get("next")),
                blockers=cls._bounded_list(progress_payload.get("blockers")) or [],
                updated_at=(
                    None
                    if progress_payload.get("updated_at") is None
                    else float(progress_payload["updated_at"])
                ),
            ),
            plan=cls._plan_from_payload(payload.get("plan")),
            in_flight_calls={
                str(call_id): {
                    "run_id": str(value.get("run_id") or ""),
                    "started_at": float(value.get("started_at") or 0.0),
                }
                for call_id, value in in_flight_payload.items()
                if isinstance(value, dict) and value.get("run_id")
            },
            activity_seq=int(payload.get("activity_seq") or 0),
            activity=deque(
                [item for item in activity_payload if isinstance(item, dict)],
                maxlen=SESSION_ACTIVITY_LIMIT,
            ),
        )

    @classmethod
    def _session_to_payload(cls, session: LogicalSession) -> dict[str, Any]:
        return {
            "version": 1,
            "session_id": session.session_id,
            "subject": session.subject,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "status": session.status,
            "label": session.label,
            "objective": session.objective,
            "active_run_id": session.active_run_id,
            "runs": [
                {
                    "run_id": run.run_id,
                    "created_at": run.created_at,
                    "updated_at": run.updated_at,
                    "status": run.status,
                }
                for run in session.runs
            ],
            "progress": asdict(session.progress),
            "plan": cls._plan_to_payload(session.plan),
            "in_flight_calls": session.in_flight_calls,
            "activity_seq": session.activity_seq,
            "activity": list(session.activity),
        }

    def _save_locked(self, session: LogicalSession) -> None:
        data = json.dumps(
            self._session_to_payload(session),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._state_store().write_bytes(f"sessions/{session.session_id}.json", data)

    @staticmethod
    def _new_session_id() -> str:
        return f"s_{secrets.token_hex(12)}"

    @staticmethod
    def _new_run_id() -> str:
        return f"r_{secrets.token_hex(5)}"

    @staticmethod
    def _authenticated_subject() -> str | None:
        principal = current_principal()
        if principal is None:
            return None
        return principal.subject or principal.email or "mcp-client"

    def _require_session_locked(self, session_id: str, subject: str | None = None) -> LogicalSession:
        self._ensure_loaded_locked()
        normalized_id = str(session_id)
        self._refresh_session_locked(normalized_id)
        session = self._sessions.get(normalized_id)
        if session is None:
            raise ValueError(f"Unknown logical session: {session_id}")
        if subject is not None and session.subject != subject:
            raise PermissionError("Logical session belongs to a different principal")
        return session

    def _append_activity_locked(
        self,
        session: LogicalSession,
        event_type: str,
        *,
        actor: str,
        data: dict[str, Any] | None = None,
        touch_plan: bool = False,
    ) -> dict[str, Any]:
        now = time.time()
        session.activity_seq += 1
        event = {
            "seq": session.activity_seq,
            "ts": now,
            "type": event_type,
            "actor": actor,
            "data": data or {},
        }
        session.activity.append(event)
        session.updated_at = now
        if touch_plan and session.plan is not None and session.plan.status == "active":
            session.plan.last_agent_activity = now
            session.plan.updated_at = max(session.plan.updated_at, now)
        self._save_locked(session)
        return event

    def _attach_new_run_locked(
        self,
        session: LogicalSession,
        session_key: str,
        *,
        takeover: bool,
    ) -> AgentRun:
        previous = self._attachments.get(session_key)
        previous_session = None
        previous_run = None
        if previous is not None:
            if previous[0] != session.session_id:
                self._refresh_session_locked(previous[0])
            previous_session = self._sessions.get(previous[0])
            if previous_session is not None:
                previous_run = next(
                    (run for run in previous_session.runs if run.run_id == previous[1]), None
                )
                if (
                    previous_session.session_id != session.session_id
                    and previous_run is not None
                    and previous_run.status == "active"
                    and self._in_flight_count_locked(previous_session.session_id)
                ):
                    raise ValueError(
                        "Cannot switch logical sessions while tool calls are still in flight; retry after they complete"
                    )

        current = session.active_run()
        if current is not None and current.status == "active":
            if current.session_key == session_key and not takeover:
                self._attachments[session_key] = (session.session_id, current.run_id)
                return current
            if not takeover:
                raise ValueError(
                    "Session already has an active agent run; retry resume with takeover=true to supersede it"
                )
            if self._in_flight_count_locked(session.session_id):
                raise ValueError(
                    "Cannot take over a logical session while tool calls are still in flight; retry after they complete"
                )
            current.status = "superseded"
            current.updated_at = time.time()
        if (
            previous_session is not None
            and previous_run is not None
            and previous_run.status == "active"
            and previous_run is not current
        ):
            previous_run.status = "detached"
            previous_run.updated_at = time.time()
            if previous_session.active_run_id == previous_run.run_id:
                previous_session.active_run_id = None
            previous_session.updated_at = previous_run.updated_at
            self._save_locked(previous_session)
        now = time.time()
        run = AgentRun(
            run_id=self._new_run_id(),
            session_key=session_key,
            created_at=now,
            updated_at=now,
        )
        session.runs.append(run)
        session.active_run_id = run.run_id
        session.runs = self._bounded_run_history(session.runs, session.active_run_id)
        session.updated_at = now
        self._attachments[session_key] = (session.session_id, run.run_id)
        return run

    @staticmethod
    def _prune_in_flight_locked(session: LogicalSession, now: float | None = None) -> None:
        current = time.time() if now is None else now
        expired = [
            call_id
            for call_id, lease in session.in_flight_calls.items()
            if current - float(lease.get("started_at") or 0.0) >= SESSION_IN_FLIGHT_LEASE_S
        ]
        for call_id in expired:
            session.in_flight_calls.pop(call_id, None)

    def _in_flight_count_locked(self, session_id: str) -> int:
        session = self._sessions.get(session_id)
        if session is None:
            return 0
        self._prune_in_flight_locked(session)
        return len(session.in_flight_calls)

    def _public_state_locked(
        self, session: LogicalSession, *, recent_activity: int = 30
    ) -> dict[str, Any]:
        return session.public_state(
            recent_activity=recent_activity,
            in_flight_calls=self._in_flight_count_locked(session.session_id),
        )

    def manage(
        self,
        session_key: str,
        subject: str,
        *,
        action: str,
        session_id: str | None = None,
        label: str | None = None,
        objective: str | None = None,
        summary: str | None = None,
        findings: list[str] | None = None,
        next: str | None = None,
        blockers: list[str] | None = None,
        takeover: bool = False,
        session_run_id: str | None = None,
        require_run_token: bool = False,
        _state_locks_held: bool = False,
    ) -> dict[str, Any]:
        normalized_action = str(action).strip().lower()
        with self._lock:
            self._ensure_loaded_locked()
            if not _state_locks_held and normalized_action not in {"get", "list"}:
                attachment = self._attachments.get(session_key)
                lock_ids: list[str] = []
                if normalized_action == "start":
                    if attachment is not None:
                        lock_ids.append(attachment[0])
                else:
                    target_id = str(session_id or (attachment[0] if attachment else ""))
                    if target_id:
                        lock_ids.append(target_id)
                    if attachment is not None and attachment[0] != target_id:
                        lock_ids.append(attachment[0])
                if self._uses_shared_state_backend() and (
                    lock_ids or normalized_action in {"start", "delete"}
                ):
                    with contextlib.ExitStack() as stack:
                        if normalized_action in {"start", "delete"}:
                            stack.enter_context(self._state_store().lock("sessions/history"))
                        stack.enter_context(self._shared_session_locks_locked(lock_ids))
                        return self.manage(
                            session_key,
                            subject,
                            action=action,
                            session_id=session_id,
                            label=label,
                            objective=objective,
                            summary=summary,
                            findings=findings,
                            next=next,
                            blockers=blockers,
                            takeover=takeover,
                            session_run_id=session_run_id,
                            require_run_token=require_run_token,
                            _state_locks_held=True,
                        )
            if normalized_action == "start":
                if self._uses_shared_state_backend():
                    self._refresh_all_sessions_locked()
                retained = sum(
                    1 for item in self._sessions.values() if item.subject == subject
                )
                if retained >= SESSION_HISTORY_LIMIT_PER_PRINCIPAL:
                    raise ValueError(
                        "Logical session history limit reached; delete an old detached or terminal session before starting another"
                    )
                previous_attachment = self._attachments.get(session_key)
                previous_snapshot = None
                if previous_attachment is not None:
                    previous_session = self._sessions.get(previous_attachment[0])
                    if previous_session is not None:
                        previous_snapshot = copy.deepcopy(previous_session)
                now = time.time()
                logical = LogicalSession(
                    session_id=self._new_session_id(),
                    subject=subject,
                    created_at=now,
                    updated_at=now,
                    label=self._bounded_text(label),
                    objective=self._bounded_text(objective),
                )
                self._sessions[logical.session_id] = logical
                try:
                    run = self._attach_new_run_locked(logical, session_key, takeover=True)
                    self._append_activity_locked(
                        logical,
                        "session.started",
                        actor="agent",
                        data={"run_id": run.run_id},
                    )
                except Exception as exc:
                    rollback_errors: list[str] = []
                    self._sessions.pop(logical.session_id, None)
                    if self._attachments.get(session_key, (None, None))[0] == logical.session_id:
                        self._attachments.pop(session_key, None)
                    try:
                        self._state_store().delete(f"sessions/{logical.session_id}.json")
                    except Exception as rollback_exc:  # noqa: BLE001 - preserve original error.
                        rollback_errors.append(
                            f"delete new session: {type(rollback_exc).__name__}: {rollback_exc}"
                        )
                    if previous_snapshot is not None and previous_attachment is not None:
                        self._sessions[previous_snapshot.session_id] = previous_snapshot
                        self._attachments[session_key] = previous_attachment
                        try:
                            self._save_locked(previous_snapshot)
                        except Exception as rollback_exc:  # noqa: BLE001 - preserve original error.
                            rollback_errors.append(
                                f"restore previous session: {type(rollback_exc).__name__}: {rollback_exc}"
                            )
                    elif previous_attachment is None:
                        self._attachments.pop(session_key, None)
                    if rollback_errors:
                        exc.add_note("Session start rollback warnings: " + "; ".join(rollback_errors))
                    raise
                return self._public_state_locked(logical)

            if normalized_action == "list":
                self._refresh_all_sessions_locked()
                sessions = [
                    item
                    for item in self._sessions.values()
                    if item.subject == subject
                ]
                sessions.sort(key=lambda item: item.updated_at, reverse=True)
                return {
                    "sessions": [
                        {
                            "session_id": item.session_id,
                            "label": (
                                item.label[:SESSION_LIST_TEXT_LIMIT]
                                if item.label is not None
                                else None
                            ),
                            "objective": (
                                item.objective[:SESSION_LIST_TEXT_LIMIT]
                                if item.objective is not None
                                else None
                            ),
                            "status": item.status,
                            "updated_at": item.updated_at,
                            "active_run": item.active_run().public_state()
                            if item.active_run()
                            else None,
                            "progress": item.progress.list_state(),
                            "goal_mode": bool(
                                item.plan and item.plan.status in {"active", "blocked"}
                            ),
                        }
                        for item in sessions[:SESSION_LIST_LIMIT]
                    ]
                }

            target_id = session_id
            if target_id is None:
                attachment = self._attachments.get(session_key)
                if attachment is not None:
                    target_id = attachment[0]
            if not target_id:
                raise ValueError(
                    "No logical session is attached. Call session_manage(action='start') or resume an existing session_id first."
                )
            logical = self._require_session_locked(target_id, subject)

            if normalized_action == "get":
                return self._public_state_locked(logical)

            if normalized_action == "delete":
                if self._in_flight_count_locked(logical.session_id):
                    raise ValueError("Cannot delete a logical session while tool calls are in flight")
                active = logical.active_run()
                if active is not None and active.status == "active":
                    raise ValueError(
                        "Cannot delete a logical session with an active agent run; finish, cancel, or switch away first"
                    )
                self._state_store().delete(f"sessions/{logical.session_id}.json")
                self._sessions.pop(logical.session_id, None)
                for key, attached in list(self._attachments.items()):
                    if attached[0] == logical.session_id:
                        self._attachments.pop(key, None)
                return {"session_id": logical.session_id, "deleted": True}

            if normalized_action == "resume":
                if logical.status != "active":
                    raise ValueError(f"Cannot resume a {logical.status} session")
                previous_attachment = self._attachments.get(session_key)
                snapshots: dict[str, LogicalSession] = {
                    logical.session_id: copy.deepcopy(logical)
                }
                if previous_attachment is not None:
                    previous_session = self._sessions.get(previous_attachment[0])
                    if (
                        previous_session is not None
                        and previous_session.session_id not in snapshots
                    ):
                        snapshots[previous_session.session_id] = copy.deepcopy(previous_session)
                try:
                    run = self._attach_new_run_locked(logical, session_key, takeover=takeover)
                    self._append_activity_locked(
                        logical,
                        "session.resumed",
                        actor="agent",
                        data={"run_id": run.run_id, "takeover": takeover},
                        touch_plan=True,
                    )
                except Exception as exc:
                    rollback_errors: list[str] = []
                    for snapshot in snapshots.values():
                        self._sessions[snapshot.session_id] = snapshot
                    if previous_attachment is None:
                        self._attachments.pop(session_key, None)
                    else:
                        self._attachments[session_key] = previous_attachment
                    for snapshot in snapshots.values():
                        try:
                            self._save_locked(snapshot)
                        except Exception as rollback_exc:  # noqa: BLE001 - preserve original error.
                            rollback_errors.append(
                                f"restore {snapshot.session_id}: {type(rollback_exc).__name__}: {rollback_exc}"
                            )
                    if rollback_errors:
                        exc.add_note("Session resume rollback warnings: " + "; ".join(rollback_errors))
                    raise
                return self._public_state_locked(logical)

            self._assert_attachment_locked(
                session_key,
                logical.session_id,
                expected_run_id=session_run_id,
                require_run_token=require_run_token,
                subject=subject,
            )
            run = logical.active_run()
            if run is None:
                raise RuntimeError("Logical session has no active agent run")

            if normalized_action == "report":
                changed = False
                if summary is not None:
                    logical.progress.summary = self._bounded_text(summary)
                    changed = True
                if findings is not None:
                    logical.progress.findings = self._bounded_list(findings) or []
                    changed = True
                if next is not None:
                    logical.progress.next = self._bounded_text(next)
                    changed = True
                if blockers is not None:
                    logical.progress.blockers = self._bounded_list(blockers) or []
                    changed = True
                if objective is not None:
                    logical.objective = self._bounded_text(objective)
                    changed = True
                if label is not None:
                    logical.label = self._bounded_text(label)
                    changed = True
                if not changed:
                    raise ValueError(
                        "action=report requires summary, findings, next, blockers, objective, or label"
                    )
                now = time.time()
                logical.progress.updated_at = now
                run.updated_at = now
                self._append_activity_locked(
                    logical,
                    "session.reported",
                    actor="agent",
                    data={
                        "run_id": run.run_id,
                        "summary": logical.progress.summary,
                        "next": logical.progress.next,
                        "blocker_count": len(logical.progress.blockers),
                    },
                    touch_plan=True,
                )
                return self._public_state_locked(logical)

            if normalized_action in {"finish", "cancel"} and self._in_flight_count_locked(
                logical.session_id
            ):
                raise ValueError(
                    f"Cannot {normalized_action} a logical session while tool calls are in flight"
                )

            if normalized_action == "finish":
                if logical.plan is not None and logical.plan.status in {"active", "blocked"}:
                    raise ValueError(
                        "Cannot finish a session while its plan is active or blocked; finish or cancel the plan first"
                    )
                logical.status = "completed"
                run.status = "completed"
                run.updated_at = time.time()
                logical.active_run_id = None
                self._attachments.pop(session_key, None)
                self._append_activity_locked(
                    logical,
                    "session.completed",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return self._public_state_locked(logical)

            if normalized_action == "cancel":
                logical.status = "cancelled"
                run.status = "cancelled"
                run.updated_at = time.time()
                logical.active_run_id = None
                if logical.plan is not None and logical.plan.status not in {"completed", "cancelled"}:
                    logical.plan.status = "cancelled"
                    logical.plan.updated_at = run.updated_at
                    logical.plan.continuation_pending = False
                    logical.plan.continuation_pending_since = None
                    logical.plan.continuation_claim_id = None
                self._attachments.pop(session_key, None)
                self._append_activity_locked(
                    logical,
                    "session.cancelled",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return self._public_state_locked(logical)

            raise ValueError(
                "action must be one of: start, resume, get, report, list, finish, cancel, delete"
            )

    def _assert_attachment_locked(
        self,
        session_key: str,
        session_id: str | None = None,
        *,
        expected_run_id: str | None = None,
        require_run_token: bool = False,
        subject: str | None = None,
    ) -> LogicalSession:
        attachment = self._attachments.get(session_key)
        if attachment is None:
            raise RuntimeError(
                "No active logical session run is attached. Resume the session before continuing."
            )
        if session_id is not None and attachment[0] != session_id:
            raise RuntimeError("Current agent run is attached to a different logical session")
        logical = self._require_session_locked(attachment[0])
        if subject is not None and logical.subject != subject:
            self._attachments.pop(session_key, None)
            raise PermissionError("Logical session belongs to a different principal")
        if require_run_token and not expected_run_id:
            raise RuntimeError(
                "session_run_id is required while a logical session is attached; use the active_run.run_id returned by session_manage"
            )
        if expected_run_id is not None and attachment[1] != expected_run_id:
            raise RuntimeError(
                "This agent run has been superseded; resume the logical session and use its new active_run.run_id"
            )
        if logical.status != "active":
            raise RuntimeError(f"Logical session is {logical.status}; start or resume another session")
        if logical.active_run_id != attachment[1]:
            raise RuntimeError(
                "This agent run has been superseded by another agent. Resume with takeover=true before continuing."
            )
        run = logical.active_run()
        if run is None or run.status != "active":
            raise RuntimeError(
                "This agent run is no longer active. Resume the logical session before continuing."
            )
        return logical

    def current_session_id(self, session_key: str, *, subject: str | None = None) -> str | None:
        with self._lock:
            self._ensure_loaded_locked()
            attachment = self._attachments.get(session_key)
            if attachment is None:
                return None
            try:
                self._assert_attachment_locked(session_key, subject=subject)
            except (RuntimeError, PermissionError):
                return None
            return attachment[0]

    def get(self, session_id: str, *, subject: str | None = None) -> dict[str, Any]:
        with self._lock:
            logical = self._require_session_locked(session_id, subject)
            return self._public_state_locked(logical)

    def plan_state(self, session_id: str | None) -> dict[str, Any] | None:
        if not session_id:
            return None
        with self._lock:
            logical = self._require_session_locked(session_id)
            return (
                logical.plan.public_state(
                    in_flight_calls=self._in_flight_count_locked(logical.session_id)
                )
                if logical.plan
                else None
            )

    def begin_tool_call(
        self,
        session_key: str,
        call_id: str,
        *,
        expected_run_id: str | None,
        subject: str | None = None,
        require_run_token: bool = True,
        data: dict[str, Any] | None = None,
        _state_lock_held: bool = False,
    ) -> dict[str, Any] | None:
        """Acquire and durably persist a per-run lease before a tool may execute.

        A start-persistence failure is fail-closed because running an external mutation
        without a durable in-flight lease would permit unsafe takeover after recovery.
        """
        with self._lock:
            self._ensure_loaded_locked()
            if session_key not in self._attachments:
                if expected_run_id is None:
                    return None
                if self._uses_shared_state_backend():
                    self._refresh_all_sessions_locked()
                matches: list[LogicalSession] = []
                for candidate in self._sessions.values():
                    if subject is not None and candidate.subject != subject:
                        continue
                    run = candidate.active_run()
                    if (
                        candidate.status == "active"
                        and candidate.active_run_id == expected_run_id
                        and run is not None
                        and run.status == "active"
                    ):
                        matches.append(candidate)
                if len(matches) != 1:
                    raise RuntimeError(
                        "This agent run is stale or unknown; resume the logical session and use its current active_run.run_id"
                    )
                recovered = matches[0]
                recovered_run = recovered.active_run()
                assert recovered_run is not None
                recovered_run.session_key = session_key
                self._attachments[session_key] = (
                    recovered.session_id,
                    recovered_run.run_id,
                )
            attachment = self._attachments[session_key]
            if not _state_lock_held and self._uses_shared_state_backend():
                with self._shared_session_locks_locked([attachment[0]]):
                    return self.begin_tool_call(
                        session_key,
                        call_id,
                        expected_run_id=expected_run_id,
                        subject=subject,
                        require_run_token=require_run_token,
                        data=data,
                        _state_lock_held=True,
                    )
            logical = self._assert_attachment_locked(
                session_key,
                expected_run_id=expected_run_id,
                require_run_token=require_run_token,
                subject=subject,
            )
            run = logical.active_run()
            if run is None:
                raise RuntimeError("Logical session has no active agent run")
            before_start = copy.deepcopy(logical)
            now = time.time()
            logical.in_flight_calls[call_id] = {"run_id": run.run_id, "started_at": now}
            run.updated_at = now
            try:
                self._append_activity_locked(
                    logical,
                    "tool.started",
                    actor="agent",
                    data={"call_id": call_id, **(data or {})},
                    touch_plan=True,
                )
            except Exception as exc:
                self._sessions[logical.session_id] = before_start
                raise RuntimeError(
                    "Failed to persist the tool-call lease; refusing to execute the tool unprotected"
                ) from exc
            return {
                "session_id": logical.session_id,
                "run_id": run.run_id,
                "call_id": call_id,
                "persistence_error": None,
            }

    def finish_tool_call(
        self,
        lease: dict[str, Any] | None,
        event_type: str,
        *,
        data: dict[str, Any] | None = None,
        _state_lock_held: bool = False,
    ) -> str | None:
        if lease is None:
            return None
        with self._lock:
            self._ensure_loaded_locked()
            session_id = str(lease.get("session_id") or "")
            run_id = str(lease.get("run_id") or "")
            call_id = str(lease.get("call_id") or "")
            if not _state_lock_held and self._uses_shared_state_backend():
                with self._shared_session_locks_locked([session_id]):
                    return self.finish_tool_call(
                        lease,
                        event_type,
                        data=data,
                        _state_lock_held=True,
                    )
            self._refresh_session_locked(session_id)
            logical = self._sessions.get(session_id)
            if logical is None:
                return None
            logical.in_flight_calls.pop(call_id, None)
            run = next((item for item in logical.runs if item.run_id == run_id), None)
            if run is not None:
                run.updated_at = time.time()
            stale_run = logical.active_run_id != run_id
            lease_persistence_error = None
            try:
                self._save_locked(logical)
            except Exception as exc:  # noqa: BLE001 - completion must not mask tool results.
                lease_persistence_error = f"{type(exc).__name__}: {exc}"
            try:
                self._append_activity_locked(
                    logical,
                    event_type,
                    actor="agent",
                    data={"call_id": call_id, "stale_run": stale_run, **(data or {})},
                    touch_plan=not stale_run,
                )
            except Exception as exc:  # noqa: BLE001 - never mask the tool result.
                activity_error = f"{type(exc).__name__}: {exc}"
                return "; ".join(
                    item for item in (lease_persistence_error, activity_error) if item
                )
            return lease_persistence_error

    @classmethod
    def _normalize_plan_steps(cls, steps: list[dict[str, Any]]) -> list[PlanStep]:
        if not steps:
            raise ValueError("A plan requires at least one step")
        if len(steps) > PLAN_MAX_STEPS:
            raise ValueError(f"A plan may contain at most {PLAN_MAX_STEPS} steps")
        normalized: list[PlanStep] = []
        seen: set[str] = set()
        for index, raw in enumerate(steps):
            step_id = cls._bounded_plan_text(
                raw.get("id") or f"step-{index + 1}", PLAN_STEP_ID_LIMIT
            )
            text = cls._bounded_plan_text(
                raw.get("text") or raw.get("content") or raw.get("title") or "",
                PLAN_STEP_TEXT_LIMIT,
            )
            status = str(raw.get("status") or "pending").strip().lower()
            note = cls._bounded_plan_text(raw.get("note"), PLAN_NOTE_LIMIT) or None
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
        session_run_id: str | None = None,
        require_run_token: bool = False,
        objective: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        step_id: str | None = None,
        status: str | None = None,
        text: str | None = None,
        note: str | None = None,
        actor: str = "agent",
        _state_lock_held: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            self._ensure_loaded_locked()
            normalized_action = action.strip().lower()
            attachment = self._attachments.get(session_key)
            if (
                not _state_lock_held
                and normalized_action != "get"
                and attachment is not None
                and self._uses_shared_state_backend()
            ):
                with self._shared_session_locks_locked([attachment[0]]):
                    return self.manage_plan(
                        session_key,
                        action=action,
                        session_run_id=session_run_id,
                        require_run_token=require_run_token,
                        objective=objective,
                        steps=steps,
                        step_id=step_id,
                        status=status,
                        text=text,
                        note=note,
                        actor=actor,
                        _state_lock_held=True,
                    )
            logical = self._assert_attachment_locked(
                session_key,
                expected_run_id=session_run_id,
                require_run_token=require_run_token and normalized_action != "get",
                subject=self._authenticated_subject(),
            )
            return self._manage_plan_locked(
                logical,
                action=action,
                objective=objective,
                steps=steps,
                step_id=step_id,
                status=status,
                text=text,
                note=note,
                actor=actor,
            )

    def manage_plan_for_session(
        self,
        session_id: str,
        *,
        action: str,
        note: str | None = None,
        actor: str = "human",
        subject: str | None = None,
        _state_lock_held: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            if (
                not _state_lock_held
                and action.strip().lower() != "get"
                and self._uses_shared_state_backend()
            ):
                with self._shared_session_locks_locked([session_id]):
                    return self.manage_plan_for_session(
                        session_id,
                        action=action,
                        note=note,
                        actor=actor,
                        subject=subject,
                        _state_lock_held=True,
                    )
            logical = self._require_session_locked(session_id, subject)
            return self._manage_plan_locked(logical, action=action, note=note, actor=actor)

    def _manage_plan_locked(
        self,
        logical: LogicalSession,
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
        plan = logical.plan
        if normalized_action == "get":
            return {
                "session_id": logical.session_id,
                "goal_mode": bool(plan and plan.status in {"active", "blocked"}),
                "plan": (
                    plan.public_state(
                        in_flight_calls=self._in_flight_count_locked(logical.session_id)
                    )
                    if plan
                    else None
                ),
            }
        now = time.time()
        event_type = ""
        event_data: dict[str, Any] = {}
        if normalized_action == "start":
            if plan is not None and plan.status in {"active", "blocked"}:
                raise ValueError("A plan is already active; finish or cancel it before starting another")
            objective_text = self._bounded_plan_text(objective, PLAN_OBJECTIVE_LIMIT)
            if not objective_text:
                raise ValueError("objective is required for action=start")
            plan = PlanState(
                plan_id=uuid.uuid4().hex,
                objective=objective_text,
                steps=self._normalize_plan_steps(list(steps or [])),
                created_at=now,
                updated_at=now,
                last_agent_activity=now,
            )
            logical.plan = plan
            if logical.objective is None:
                logical.objective = objective_text[:SESSION_TEXT_LIMIT]
            event_type = "plan.started"
            event_data = {"plan_id": plan.plan_id, "objective": plan.objective}
        else:
            if plan is None:
                raise ValueError("No plan exists in this logical session")
            if normalized_action == "update":
                if plan.status not in {"active", "blocked"}:
                    raise ValueError(f"Cannot update a {plan.status} plan")
                changed = False
                if objective is not None:
                    objective_text = self._bounded_plan_text(objective, PLAN_OBJECTIVE_LIMIT)
                    if not objective_text:
                        raise ValueError("objective cannot be empty")
                    plan.objective = objective_text
                    changed = True
                if steps is not None:
                    plan.steps = self._normalize_plan_steps(list(steps))
                    changed = True
                if step_id is not None:
                    normalized_step_id = self._bounded_plan_text(step_id, PLAN_STEP_ID_LIMIT)
                    target = next(
                        (step for step in plan.steps if step.id == normalized_step_id), None
                    )
                    if target is None:
                        raise ValueError(f"Unknown plan step: {normalized_step_id}")
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
                        normalized_text = self._bounded_plan_text(text, PLAN_STEP_TEXT_LIMIT)
                        if not normalized_text:
                            raise ValueError("step text cannot be empty")
                        target.text = normalized_text
                        changed = True
                    if note is not None:
                        target.note = self._bounded_plan_text(note, PLAN_NOTE_LIMIT) or None
                        changed = True
                elif status is not None or text is not None:
                    raise ValueError("step_id is required when updating step status or text")
                if note is not None and step_id is None:
                    plan.note = self._bounded_plan_text(note, PLAN_NOTE_LIMIT) or None
                    changed = True
                if not changed:
                    raise ValueError("action=update requires objective, steps, step_id, or note")
                self._promote_next_step(plan)
                plan.revision += 1
                plan.updated_at = now
                plan.last_agent_activity = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
                plan.continuation_retry_after = None
                event_type = "plan.updated"
                event_data = {"plan_id": plan.plan_id, "revision": plan.revision}
            elif normalized_action == "block":
                if plan.status != "active":
                    raise ValueError(f"Cannot block a {plan.status} plan")
                reason = self._bounded_plan_text(note, PLAN_NOTE_LIMIT)
                if not reason:
                    raise ValueError("note is required for action=block")
                plan.status = "blocked"
                plan.note = reason
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
                event_type = "plan.blocked"
                event_data = {"plan_id": plan.plan_id, "reason": reason}
            elif normalized_action == "resume":
                if plan.status != "blocked":
                    raise ValueError("Only a blocked plan can be resumed")
                plan.status = "active"
                plan.note = None
                plan.revision += 1
                plan.updated_at = now
                if actor == "agent":
                    plan.last_agent_activity = now
                plan.continuation_retry_after = None
                event_type = "plan.resumed"
                event_data = {"plan_id": plan.plan_id}
            elif normalized_action == "finish":
                if plan.status not in {"active", "blocked"}:
                    raise ValueError(f"Cannot finish a {plan.status} plan")
                unfinished = [step.id for step in plan.steps if step.status in {"pending", "active"}]
                if unfinished:
                    raise ValueError(
                        "Cannot finish plan while unfinished steps remain: " + ", ".join(unfinished)
                    )
                plan.status = "completed"
                plan.note = self._bounded_plan_text(note, PLAN_NOTE_LIMIT) or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
                plan.continuation_retry_after = None
                event_type = "plan.completed"
                event_data = {"plan_id": plan.plan_id}
            elif normalized_action == "cancel":
                if plan.status in {"completed", "cancelled"}:
                    raise ValueError(f"Plan is already {plan.status}")
                plan.status = "cancelled"
                plan.note = self._bounded_plan_text(note, PLAN_NOTE_LIMIT) or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
                plan.continuation_retry_after = None
                event_type = "plan.cancelled"
                event_data = {"plan_id": plan.plan_id}
            else:
                raise ValueError(
                    "action must be one of: start, get, update, block, resume, finish, cancel"
                )
        self._append_activity_locked(
            logical,
            event_type,
            actor=actor,
            data=event_data,
            touch_plan=actor == "agent" and normalized_action not in {"block", "finish", "cancel"},
        )
        return {
            "session_id": logical.session_id,
            "goal_mode": plan.status in {"active", "blocked"},
            "plan": plan.public_state(
                now, in_flight_calls=self._in_flight_count_locked(logical.session_id)
            ),
        }

    def claim_plan_continuation(
        self,
        session_id: str,
        *,
        subject: str | None = None,
        _state_lock_held: bool = False,
    ) -> dict[str, Any] | None:
        with self._lock:
            if not _state_lock_held and self._uses_shared_state_backend():
                with self._shared_session_locks_locked([session_id]):
                    return self.claim_plan_continuation(
                        session_id,
                        subject=subject,
                        _state_lock_held=True,
                    )
            logical = self._require_session_locked(session_id, subject)
            plan = logical.plan
            if plan is None or plan.status != "active":
                return None
            now = time.time()
            if self._in_flight_count_locked(logical.session_id):
                return None
            if plan.continuation_pending:
                pending_since = plan.continuation_pending_since or now
                if now - pending_since < PLAN_CONTINUATION_PENDING_TTL_S:
                    return None
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
            if plan.continuation_count >= PLAN_MAX_CONTINUATIONS:
                return None
            if plan.continuation_retry_after is not None and now < plan.continuation_retry_after:
                return None
            if now < plan.last_agent_activity + PLAN_EXECUTION_LEASE_S:
                return None
            plan.continuation_pending = True
            plan.continuation_pending_since = now
            plan.continuation_claim_id = f"c_{secrets.token_hex(8)}"
            plan.updated_at = now
            self._append_activity_locked(
                logical,
                "plan.continuation_requested",
                actor="system",
                data={"plan_id": plan.plan_id, "attempt": plan.continuation_count + 1},
            )
            return {
                "session_id": logical.session_id,
                "plan": plan.public_state(
                    now, in_flight_calls=self._in_flight_count_locked(logical.session_id)
                ),
                "recent_events": list(logical.activity)[-20:],
                "continuation_count": plan.continuation_count + 1,
                "claim_id": plan.continuation_claim_id,
            }

    def validate_plan_continuation(
        self,
        session_id: str,
        claim_id: str,
        *,
        subject: str | None = None,
        _state_lock_held: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            if not _state_lock_held and self._uses_shared_state_backend():
                with self._shared_session_locks_locked([session_id]):
                    return self.validate_plan_continuation(
                        session_id,
                        claim_id,
                        subject=subject,
                        _state_lock_held=True,
                    )
            logical = self._require_session_locked(session_id, subject)
            plan = logical.plan
            now = time.time()
            in_flight_calls = self._in_flight_count_locked(logical.session_id)
            valid = bool(
                plan is not None
                and plan.status == "active"
                and plan.continuation_pending
                and plan.continuation_claim_id == claim_id
                and in_flight_calls == 0
                and now >= plan.last_agent_activity + PLAN_EXECUTION_LEASE_S
            )
            if (
                plan is not None
                and plan.continuation_pending
                and plan.continuation_claim_id == claim_id
                and not valid
            ):
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                plan.continuation_claim_id = None
                plan.updated_at = now
                self._save_locked(logical)
            return {
                "valid": valid,
                "session_id": logical.session_id,
                "plan": (
                    plan.public_state(now, in_flight_calls=in_flight_calls)
                    if plan is not None
                    else None
                ),
            }

    def report_plan_continuation(
        self,
        session_id: str,
        *,
        accepted: bool,
        error: str | None = None,
        claim_id: str | None = None,
        subject: str | None = None,
        _state_lock_held: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            if not _state_lock_held and self._uses_shared_state_backend():
                with self._shared_session_locks_locked([session_id]):
                    return self.report_plan_continuation(
                        session_id,
                        accepted=accepted,
                        error=error,
                        claim_id=claim_id,
                        subject=subject,
                        _state_lock_held=True,
                    )
            logical = self._require_session_locked(session_id, subject)
            plan = logical.plan
            if plan is None:
                raise ValueError("No plan exists in this logical session")
            if not plan.continuation_pending:
                raise ValueError("No plan continuation is pending")
            if claim_id is not None and plan.continuation_claim_id != claim_id:
                raise ValueError("Plan continuation claim is stale")
            now = time.time()
            plan.continuation_pending = False
            plan.continuation_pending_since = None
            plan.continuation_claim_id = None
            plan.continuation_count += 1
            plan.last_continuation_at = now
            if accepted:
                plan.last_agent_activity = now
                plan.continuation_retry_after = None
            else:
                plan.continuation_retry_after = now + PLAN_CONTINUATION_FAILURE_BACKOFF_S
            plan.updated_at = now
            self._append_activity_locked(
                logical,
                "plan.continuation_sent" if accepted else "plan.continuation_failed",
                actor="system",
                data={
                    "plan_id": plan.plan_id,
                    "count": plan.continuation_count,
                    **({"error": error[:500]} if error else {}),
                },
            )
            return plan.public_state(
                now, in_flight_calls=self._in_flight_count_locked(logical.session_id)
            )


_MANAGER = SessionRuntimeManager()


def get_session_runtime_manager() -> SessionRuntimeManager:
    return _MANAGER
