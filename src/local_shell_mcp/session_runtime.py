from __future__ import annotations

import contextlib
import json
import os
import secrets
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .settings import get_settings

PLAN_EXECUTION_LEASE_S = 15 * 60
PLAN_MAX_CONTINUATIONS = 10
PLAN_CONTINUATION_PENDING_TTL_S = 5 * 60
PLAN_MAX_STEPS = 100
PLAN_STEP_STATUSES = frozenset({"pending", "active", "completed", "skipped"})
SESSION_ACTIVITY_LIMIT = 200
SESSION_REPORT_LIST_LIMIT = 50
SESSION_TEXT_LIMIT = 20_000
SESSION_LIST_LIMIT = 100


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
    activity_seq: int = 0
    activity: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=SESSION_ACTIVITY_LIMIT)
    )

    def active_run(self) -> AgentRun | None:
        if not self.active_run_id:
            return None
        return next((run for run in self.runs if run.run_id == self.active_run_id), None)

    def public_state(self, *, recent_activity: int = 30) -> dict[str, Any]:
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
            "plan": self.plan.public_state() if self.plan else None,
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
        self._loaded_dir: Path | None = None
        self._sessions: dict[str, LogicalSession] = {}
        self._attachments: dict[str, tuple[str, str]] = {}

    def _session_dir(self) -> Path:
        base = self._state_dir_override or get_settings().state_dir
        return Path(base) / "sessions"

    def _ensure_loaded_locked(self) -> None:
        directory = self._session_dir()
        if self._loaded_dir == directory:
            return
        self._sessions.clear()
        self._attachments.clear()
        self._loaded_dir = directory
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                session = self._session_from_payload(payload)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            self._sessions[session.session_id] = session

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
            "last_continuation_at": plan.last_continuation_at,
            "last_agent_activity": plan.last_agent_activity,
        }

    @staticmethod
    def _plan_from_payload(payload: Any) -> PlanState | None:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise ValueError("invalid plan state")
        steps_payload = payload.get("steps")
        if not isinstance(steps_payload, list):
            raise ValueError("invalid plan steps")
        return PlanState(
            plan_id=str(payload["plan_id"]),
            objective=str(payload["objective"]),
            steps=[
                PlanStep(
                    id=str(step["id"]),
                    text=str(step["text"]),
                    status=str(step.get("status") or "pending"),
                    note=None if step.get("note") is None else str(step["note"]),
                )
                for step in steps_payload
                if isinstance(step, dict)
            ],
            created_at=float(payload["created_at"]),
            updated_at=float(payload["updated_at"]),
            status=str(payload.get("status") or "active"),
            revision=int(payload.get("revision") or 1),
            note=None if payload.get("note") is None else str(payload["note"]),
            continuation_count=int(payload.get("continuation_count") or 0),
            continuation_pending=bool(payload.get("continuation_pending")),
            continuation_pending_since=(
                None
                if payload.get("continuation_pending_since") is None
                else float(payload["continuation_pending_since"])
            ),
            last_continuation_at=(
                None
                if payload.get("last_continuation_at") is None
                else float(payload["last_continuation_at"])
            ),
            last_agent_activity=float(payload.get("last_agent_activity") or 0.0),
        )

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
        return LogicalSession(
            session_id=str(payload["session_id"]),
            subject=str(payload["subject"]),
            created_at=float(payload["created_at"]),
            updated_at=float(payload["updated_at"]),
            status=str(payload.get("status") or "active"),
            label=cls._bounded_text(payload.get("label")),
            objective=cls._bounded_text(payload.get("objective")),
            active_run_id=(
                None if payload.get("active_run_id") is None else str(payload["active_run_id"])
            ),
            runs=[
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
            "activity_seq": session.activity_seq,
            "activity": list(session.activity),
        }

    def _save_locked(self, session: LogicalSession) -> None:
        directory = self._session_dir()
        directory.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            directory.chmod(0o700)
        path = directory / f"{session.session_id}.json"
        temporary = directory / f".{session.session_id}.{os.getpid()}.{threading.get_ident()}.tmp"
        data = json.dumps(
            self._session_to_payload(session),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(data)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            with contextlib.suppress(OSError):
                path.chmod(0o600)
        except Exception:
            with contextlib.suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _new_session_id() -> str:
        return f"s_{secrets.token_hex(12)}"

    @staticmethod
    def _new_run_id() -> str:
        return f"r_{secrets.token_hex(5)}"

    def _require_session_locked(self, session_id: str, subject: str | None = None) -> LogicalSession:
        self._ensure_loaded_locked()
        session = self._sessions.get(str(session_id))
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
        current = session.active_run()
        if current is not None and current.status == "active":
            if current.session_key == session_key:
                self._attachments[session_key] = (session.session_id, current.run_id)
                return current
            if not takeover:
                raise ValueError(
                    "Session already has an active agent run; retry resume with takeover=true to supersede it"
                )
            current.status = "superseded"
            current.updated_at = time.time()
        previous = self._attachments.get(session_key)
        if previous is not None:
            previous_session = self._sessions.get(previous[0])
            if previous_session is not None:
                previous_run = next(
                    (run for run in previous_session.runs if run.run_id == previous[1]), None
                )
                if previous_run is not None and previous_run.status == "active":
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
        session.updated_at = now
        self._attachments[session_key] = (session.session_id, run.run_id)
        return run

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
    ) -> dict[str, Any]:
        normalized_action = str(action).strip().lower()
        with self._lock:
            self._ensure_loaded_locked()
            if normalized_action == "start":
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
                run = self._attach_new_run_locked(logical, session_key, takeover=True)
                self._append_activity_locked(
                    logical,
                    "session.started",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return logical.public_state()

            if normalized_action == "list":
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
                            "label": item.label,
                            "objective": item.objective,
                            "status": item.status,
                            "updated_at": item.updated_at,
                            "active_run": item.active_run().public_state()
                            if item.active_run()
                            else None,
                            "progress": item.progress.public_state(),
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
                return logical.public_state()

            if normalized_action == "resume":
                if logical.status != "active":
                    raise ValueError(f"Cannot resume a {logical.status} session")
                run = self._attach_new_run_locked(logical, session_key, takeover=takeover)
                self._append_activity_locked(
                    logical,
                    "session.resumed",
                    actor="agent",
                    data={"run_id": run.run_id, "takeover": takeover},
                )
                return logical.public_state()

            self._assert_attachment_locked(session_key, logical.session_id)
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
                return logical.public_state()

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
                return logical.public_state()

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
                self._attachments.pop(session_key, None)
                self._append_activity_locked(
                    logical,
                    "session.cancelled",
                    actor="agent",
                    data={"run_id": run.run_id},
                )
                return logical.public_state()

            raise ValueError(
                "action must be one of: start, resume, get, report, list, finish, cancel"
            )

    def _assert_attachment_locked(self, session_key: str, session_id: str | None = None) -> LogicalSession:
        attachment = self._attachments.get(session_key)
        if attachment is None:
            raise RuntimeError(
                "No active logical session run is attached. Resume the session before continuing."
            )
        if session_id is not None and attachment[0] != session_id:
            raise RuntimeError("Current agent run is attached to a different logical session")
        logical = self._require_session_locked(attachment[0])
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

    def assert_current_run(self, session_key: str) -> None:
        with self._lock:
            self._ensure_loaded_locked()
            if session_key not in self._attachments:
                return
            self._assert_attachment_locked(session_key)

    def current_session_id(self, session_key: str) -> str | None:
        with self._lock:
            self._ensure_loaded_locked()
            attachment = self._attachments.get(session_key)
            if attachment is None:
                return None
            try:
                self._assert_attachment_locked(session_key)
            except RuntimeError:
                return None
            return attachment[0]

    def get(self, session_id: str, *, subject: str | None = None) -> dict[str, Any]:
        with self._lock:
            logical = self._require_session_locked(session_id, subject)
            return logical.public_state()

    def plan_state(self, session_id: str | None) -> dict[str, Any] | None:
        if not session_id:
            return None
        with self._lock:
            logical = self._require_session_locked(session_id)
            return logical.plan.public_state() if logical.plan else None

    def record_activity(
        self,
        session_key: str,
        event_type: str,
        *,
        actor: str = "agent",
        data: dict[str, Any] | None = None,
        touch_plan: bool = True,
    ) -> dict[str, Any] | None:
        with self._lock:
            self._ensure_loaded_locked()
            attachment = self._attachments.get(session_key)
            if attachment is None:
                return None
            try:
                logical = self._assert_attachment_locked(session_key)
            except RuntimeError:
                return None
            run = logical.active_run()
            if run is not None:
                run.updated_at = time.time()
            return self._append_activity_locked(
                logical,
                event_type,
                actor=actor,
                data=data,
                touch_plan=touch_plan and actor == "agent",
            )

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
            self._ensure_loaded_locked()
            logical = self._assert_attachment_locked(session_key)
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
    ) -> dict[str, Any]:
        with self._lock:
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
                "plan": plan.public_state() if plan else None,
            }
        now = time.time()
        event_type = ""
        event_data: dict[str, Any] = {}
        if normalized_action == "start":
            if plan is not None and plan.status in {"active", "blocked"}:
                raise ValueError("A plan is already active; finish or cancel it before starting another")
            objective_text = str(objective or "").strip()
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
                plan.last_agent_activity = now
                event_type = "plan.updated"
                event_data = {"plan_id": plan.plan_id, "revision": plan.revision}
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
                event_type = "plan.blocked"
                event_data = {"plan_id": plan.plan_id, "reason": reason}
            elif normalized_action == "resume":
                if plan.status != "blocked":
                    raise ValueError("Only a blocked plan can be resumed")
                plan.status = "active"
                plan.note = None
                plan.revision += 1
                plan.updated_at = now
                plan.last_agent_activity = now
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
                plan.note = str(note or "").strip() or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
                event_type = "plan.completed"
                event_data = {"plan_id": plan.plan_id}
            elif normalized_action == "cancel":
                if plan.status in {"completed", "cancelled"}:
                    raise ValueError(f"Plan is already {plan.status}")
                plan.status = "cancelled"
                plan.note = str(note or "").strip() or plan.note
                plan.revision += 1
                plan.updated_at = now
                plan.continuation_pending = False
                plan.continuation_pending_since = None
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
            "plan": plan.public_state(now),
        }

    def claim_plan_continuation(self, session_id: str, *, subject: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            logical = self._require_session_locked(session_id, subject)
            plan = logical.plan
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
            self._append_activity_locked(
                logical,
                "plan.continuation_requested",
                actor="system",
                data={"plan_id": plan.plan_id, "attempt": plan.continuation_count + 1},
            )
            return {
                "session_id": logical.session_id,
                "plan": plan.public_state(now),
                "recent_events": list(logical.activity)[-20:],
                "continuation_count": plan.continuation_count + 1,
            }

    def report_plan_continuation(
        self,
        session_id: str,
        *,
        accepted: bool,
        error: str | None = None,
        subject: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            logical = self._require_session_locked(session_id, subject)
            plan = logical.plan
            if plan is None:
                raise ValueError("No plan exists in this logical session")
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
            return plan.public_state(now)


_MANAGER = SessionRuntimeManager()


def get_session_runtime_manager() -> SessionRuntimeManager:
    return _MANAGER
