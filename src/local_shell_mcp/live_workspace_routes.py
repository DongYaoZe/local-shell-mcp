from __future__ import annotations

import asyncio
from typing import Any

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .auth import Principal, current_principal, require_scopes, verify_request
from .live_workspace import LIVE_API_PREFIX, get_live_workspace_manager, workspace_id_from_claims
from .models import CommandResult
from .remote import remote_manager
from .settings import get_settings
from .shell_ops import run_shell


def _principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None) or current_principal()
    if principal is None:
        principal = verify_request(request)
    return principal


def _live_workspace(request: Request):  # noqa: ANN202
    principal = _principal(request)
    workspace_id = workspace_id_from_claims(principal.claims)
    if not workspace_id:
        raise HTTPException(status_code=403, detail="A live-workspace token is required")
    workspace = get_live_workspace_manager().by_id(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=401, detail="Live workspace expired")
    return principal, workspace


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
        principal, workspace = _live_workspace(request)
        require_scopes(principal, ("shell:read",))
        manager = get_live_workspace_manager()
        after = max(0, workspace.seq - 300)
        return _ok(
            {
                "workspace": workspace.public_state(),
                "events": manager.events_since(workspace, after, 300),
            }
        )
    except Exception as exc:
        return _error(exc)


async def live_events(request: Request) -> Response:
    try:
        principal, workspace = _live_workspace(request)
        require_scopes(principal, ("shell:read",))
        try:
            after = max(0, int(request.query_params.get("after", "0")))
            timeout_s = min(30.0, max(1.0, float(request.query_params.get("timeout", "25"))))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid event cursor") from exc
        events = await get_live_workspace_manager().wait_events(workspace, after, timeout_s)
        return _ok(
            {
                "events": events,
                "cursor": events[-1]["seq"] if events else max(after, workspace.seq),
                "control": workspace.control,
            }
        )
    except Exception as exc:
        return _error(exc)


async def live_control(request: Request) -> Response:
    try:
        _, workspace = _live_workspace(request)
        body = await request.json()
        control = str(body.get("control") or "")
        return _ok(get_live_workspace_manager().set_control(workspace, control))
    except Exception as exc:
        return _error(exc)


async def live_git(request: Request) -> Response:
    try:
        principal, workspace = _live_workspace(request)
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
        diff_data.update(
            {
                "ok": diff.ok and staged_diff.ok,
                "exit_code": diff.exit_code if not diff.ok else staged_diff.exit_code,
                "timed_out": diff.timed_out or staged_diff.timed_out,
                "duration_ms": diff.duration_ms + staged_diff.duration_ms,
                "command": "git diff --no-ext-diff --unified=3; git diff --cached --no-ext-diff --unified=3",
                "stdout": f"{diff.stdout}\n--- STAGED ---\n{staged_diff.stdout}",
                "stderr": "\n".join(
                    part for part in (diff.stderr, staged_diff.stderr) if part
                ),
                "truncated": diff.truncated or staged_diff.truncated,
            }
        )
        get_live_workspace_manager().publish_workspace(
            workspace.workspace_id,
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


def live_workspace_routes() -> list[Any]:
    return [
        Route(LIVE_API_PREFIX + "/snapshot", live_snapshot, methods=["GET"]),
        Route(LIVE_API_PREFIX + "/events", live_events, methods=["GET"]),
        Route(LIVE_API_PREFIX + "/control", live_control, methods=["POST"]),
        Route(LIVE_API_PREFIX + "/git", live_git, methods=["GET"]),
    ]
