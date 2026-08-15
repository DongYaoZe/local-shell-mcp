from __future__ import annotations

import asyncio
from typing import Any

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .auth import Principal, current_principal, require_scopes, verify_request
from .live_channel import LIVE_API_PREFIX, get_live_channel_manager, live_id_from_claims
from .models import CommandResult
from .remote import remote_manager
from .session_runtime import get_session_runtime_manager
from .settings import get_settings
from .shell_ops import run_shell


def _principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None) or current_principal()
    if principal is None:
        principal = verify_request(request)
    return principal


def _live_channel(request: Request):  # noqa: ANN202
    principal = _principal(request)
    live_id = live_id_from_claims(principal.claims)
    if not live_id:
        raise HTTPException(status_code=403, detail="A live-workspace token is required")
    channel = get_live_channel_manager().by_id(live_id)
    if channel is None:
        raise HTTPException(status_code=401, detail="Live workspace expired")
    return principal, channel


def _ok(data: Any) -> JSONResponse:
    return JSONResponse(
        {"ok": True, "data": data},
        headers={"Cache-Control": "no-store"},
    )


def _error(exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return JSONResponse(
            {"ok": False, "message": str(exc.detail)},
            status_code=exc.status_code,
            headers={"Cache-Control": "no-store", **(exc.headers or {})},
        )
    return JSONResponse(
        {"ok": False, "message": str(exc) or type(exc).__name__},
        status_code=400,
        headers={"Cache-Control": "no-store"},
    )


async def _run_machine_shell(
    machine: str,
    command: str,
    *,
    cwd: str,
    timeout_s: int,
    max_output_bytes: int,
) -> CommandResult:
    if machine == "local":
        if get_settings().disable_local:
            raise RuntimeError("Local access is disabled; select a remote machine")
        return await run_shell(
            command,
            cwd=cwd,
            timeout_s=timeout_s,
            max_output_bytes=max_output_bytes,
        )
    response = await remote_manager().call(
        machine,
        "run_shell_tool",
        {
            "command": command,
            "cwd": cwd,
            "timeout_s": timeout_s,
            "max_output_bytes": max_output_bytes,
            "_human": True,
        },
        timeout_s=max(timeout_s, get_settings().ui_remote_request_timeout_s),
    )
    if not response.get("ok", False):
        raise RuntimeError(response.get("message") or f"Remote Git inspection failed on {machine}")
    data = response.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"Remote Git inspection returned invalid data on {machine}")
    return CommandResult(**data)


async def live_snapshot(request: Request) -> Response:
    try:
        principal, channel = _live_channel(request)
        require_scopes(principal, ("shell:read",))
        manager = get_live_channel_manager()
        after = max(0, channel.seq - 300)
        channel_state = await asyncio.to_thread(channel.public_state)
        return _ok(
            {
                "channel": channel_state,
                "events": manager.events_since(channel, after, 300),
            }
        )
    except Exception as exc:
        return _error(exc)


async def live_events(request: Request) -> Response:
    try:
        principal, channel = _live_channel(request)
        require_scopes(principal, ("shell:read",))
        try:
            after = max(0, int(request.query_params.get("after", "0")))
            timeout_s = min(30.0, max(1.0, float(request.query_params.get("timeout", "25"))))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid event cursor") from exc
        events = await get_live_channel_manager().wait_events(channel, after, timeout_s)
        logical_session_id = channel.logical_session_id
        session_state = None
        if logical_session_id:
            session_state = await asyncio.to_thread(
                get_session_runtime_manager().get,
                logical_session_id,
                subject=channel.subject,
            )
        return _ok(
            {
                "events": events,
                "cursor": events[-1]["seq"] if events else after,
                "plan": session_state.get("plan") if session_state else None,
                "session": session_state,
                "session_id": logical_session_id,
            }
        )
    except Exception as exc:
        return _error(exc)


async def live_plan_control(request: Request) -> Response:
    try:
        principal, channel = _live_channel(request)
        require_scopes(principal, ("shell:read", "shell:write"))
        body = await request.json()
        action = str(body.get("action") or "").strip().lower()
        if not channel.logical_session_id:
            raise HTTPException(status_code=409, detail="Live Workspace is not attached to a logical session")
        session_manager = get_session_runtime_manager()
        live_manager = get_live_channel_manager()
        if action == "pause":
            note = str(body.get("note") or "Paused by user").strip() or "Paused by user"
            result = await asyncio.to_thread(
                session_manager.manage_plan_for_session,
                channel.logical_session_id,
                action="block",
                note=note,
                actor="human",
                subject=channel.subject,
            )
            live_manager.publish_channel(
                channel.live_id,
                "plan.blocked",
                actor="human",
                data={"plan_id": result["plan"]["plan_id"]},
            )
            return _ok(result)
        if action == "resume":
            result = await asyncio.to_thread(
                session_manager.manage_plan_for_session,
                channel.logical_session_id,
                action="resume",
                actor="human",
                subject=channel.subject,
            )
            live_manager.publish_channel(
                channel.live_id,
                "plan.resumed",
                actor="human",
                data={"plan_id": result["plan"]["plan_id"]},
            )
            return _ok(result)
        if action == "cancel":
            note = str(body.get("note") or "Cancelled by user").strip() or "Cancelled by user"
            result = await asyncio.to_thread(
                session_manager.manage_plan_for_session,
                channel.logical_session_id,
                action="cancel",
                note=note,
                actor="human",
                subject=channel.subject,
            )
            live_manager.publish_channel(
                channel.live_id,
                "plan.cancelled",
                actor="human",
                data={"plan_id": result["plan"]["plan_id"]},
            )
            return _ok(result)
        raise HTTPException(status_code=400, detail="action must be pause, resume, or cancel")
    except Exception as exc:
        return _error(exc)


async def live_plan_continuation(request: Request) -> Response:
    try:
        principal, channel = _live_channel(request)
        require_scopes(principal, ("shell:read",))
        body = await request.json()
        action = str(body.get("action") or "claim").strip().lower()
        session_manager = get_session_runtime_manager()
        if not channel.logical_session_id:
            return _ok({"claimed": False, "plan": None, "session_id": None})
        if action == "claim":
            claimed = await asyncio.to_thread(
                session_manager.claim_plan_continuation,
                channel.logical_session_id,
                subject=channel.subject,
            )
            if claimed is None:
                return _ok(
                    {
                        "claimed": False,
                        "plan": await asyncio.to_thread(
                            session_manager.plan_state, channel.logical_session_id
                        ),
                        "session_id": channel.logical_session_id,
                    }
                )
            return _ok({"claimed": True, **claimed})
        if action == "validate":
            claim_id = str(body.get("claim_id") or "").strip()
            if not claim_id:
                raise HTTPException(status_code=400, detail="claim_id is required")
            return _ok(
                await asyncio.to_thread(
                    session_manager.validate_plan_continuation,
                    channel.logical_session_id,
                    claim_id,
                    subject=channel.subject,
                )
            )
        if action == "report":
            accepted = bool(body.get("accepted"))
            error = str(body.get("error") or "").strip() or None
            claim_id = str(body.get("claim_id") or "").strip() or None
            return _ok(
                {
                    "session_id": channel.logical_session_id,
                    "plan": await asyncio.to_thread(
                        session_manager.report_plan_continuation,
                        channel.logical_session_id,
                        accepted=accepted,
                        error=error,
                        claim_id=claim_id,
                        subject=channel.subject,
                    ),
                }
            )
        raise HTTPException(status_code=400, detail="action must be claim, validate, or report")
    except Exception as exc:
        return _error(exc)


async def live_git(request: Request) -> Response:
    try:
        principal, channel = _live_channel(request)
        machine = str(request.query_params.get("machine") or "local")
        required_scopes = ("shell:read", "remote:use") if machine != "local" else ("shell:read",)
        require_scopes(principal, required_scopes)
        cwd = str(request.query_params.get("cwd") or ".")
        status_task = _run_machine_shell(
            machine,
            "git status --short --branch",
            cwd=cwd,
            timeout_s=15,
            max_output_bytes=80_000,
        )
        diff_task = _run_machine_shell(
            machine,
            "git diff --no-ext-diff --unified=3",
            cwd=cwd,
            timeout_s=20,
            max_output_bytes=250_000,
        )
        staged_diff_task = _run_machine_shell(
            machine,
            "git diff --cached --no-ext-diff --unified=3",
            cwd=cwd,
            timeout_s=20,
            max_output_bytes=100_000,
        )
        status, diff, staged_diff = await asyncio.gather(
            status_task, diff_task, staged_diff_task
        )
        diff_data = diff.model_dump()
        combined_stdout = diff.stdout
        if staged_diff.stdout:
            if combined_stdout and not combined_stdout.endswith("\n"):
                combined_stdout += "\n"
            combined_stdout += f"--- STAGED ---\n{staged_diff.stdout}"
        diff_data.update(
            {
                "ok": diff.ok and staged_diff.ok,
                "exit_code": diff.exit_code if not diff.ok else staged_diff.exit_code,
                "timed_out": diff.timed_out or staged_diff.timed_out,
                "duration_ms": diff.duration_ms + staged_diff.duration_ms,
                "command": "git diff --no-ext-diff --unified=3; git diff --cached --no-ext-diff --unified=3",
                "stdout": combined_stdout,
                "stderr": "\n".join(
                    part for part in (diff.stderr, staged_diff.stderr) if part
                ),
                "truncated": diff.truncated or staged_diff.truncated,
            }
        )
        get_live_channel_manager().publish_channel(
            channel.live_id,
            "human.inspected_diff",
            actor="human",
            data={"machine": machine, "cwd": cwd},
        )
        return _ok(
            {
                "machine": machine,
                "cwd": cwd,
                "status": status.model_dump(),
                "diff": diff_data,
            }
        )
    except Exception as exc:
        return _error(exc)


def live_channel_routes() -> list[Any]:
    return [
        Route(LIVE_API_PREFIX + "/snapshot", live_snapshot, methods=["GET"]),
        Route(LIVE_API_PREFIX + "/events", live_events, methods=["GET"]),
        Route(LIVE_API_PREFIX + "/plan", live_plan_control, methods=["POST"]),
        Route(LIVE_API_PREFIX + "/plan/continuation", live_plan_continuation, methods=["POST"]),
        Route(LIVE_API_PREFIX + "/git", live_git, methods=["GET"]),
    ]
