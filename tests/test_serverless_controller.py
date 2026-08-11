from __future__ import annotations

import asyncio
import base64
import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

import local_shell_mcp.audit as audit_module
import local_shell_mcp.jobs as jobs_module
import local_shell_mcp.oauth as oauth_module
import local_shell_mcp.remote as remote_module
import local_shell_mcp.tools as tools
import local_shell_mcp.ui_security as ui_security
from local_shell_mcp.dynamic_mcp import DynamicMCPManager
from local_shell_mcp.peer_transfer import open_peer_receiver
from local_shell_mcp.settings import get_settings
from local_shell_mcp.state_store import clear_memory_state, get_state_store
from local_shell_mcp.transfer_ops import transfer_stat


def _configure_stateless(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATELESS_CONTROLLER", "true")
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_OAUTH_JWT_SECRET", "s" * 48)
    monkeypatch.setenv("LOCAL_SHELL_MCP_PUBLIC_BASE_URL", "https://controller.test")
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX", f"test-{tmp_path.name}")
    for key, value in env.items():
        monkeypatch.setenv("LOCAL_SHELL_MCP_" + key.upper(), value)
    get_settings.cache_clear()
    clear_memory_state()


def _configure_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **env: str) -> Path:
    root = tmp_path / "workspace"
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(root))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_OAUTH_JWT_SECRET", "s" * 48)
    for key, value in env.items():
        monkeypatch.setenv("LOCAL_SHELL_MCP_" + key.upper(), value)
    get_settings.cache_clear()
    get_settings()
    return root


def test_stateless_settings_require_no_persistent_directories(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch)

    settings = get_settings()

    assert settings.stateless_controller is True
    assert settings.disable_local is True
    assert settings.state_backend == "memory"
    assert settings.file_download_enabled is False
    assert settings.ui_wallpaper == "none"
    assert not settings.workspace_root.exists()
    assert not settings.state_dir.exists()


def test_stateless_requires_explicit_signing_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATELESS_CONTROLLER", "true")
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("LOCAL_SHELL_MCP_OAUTH_JWT_SECRET", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="OAUTH_JWT_SECRET"):
        get_settings()


def test_stateless_ui_local_token_uses_state_backend(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch)

    token = ui_security.get_or_create_ui_local_token()

    assert len(token) >= 32
    assert get_state_store().read_bytes("ui/local-token") == token.encode("utf-8")
    assert not get_settings().state_dir.exists()


@pytest.mark.asyncio
async def test_stateless_rejects_dynamic_stdio_mcp(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch)
    manager = DynamicMCPManager(get_settings().state_dir)

    with pytest.raises(ValueError, match="stdio dynamic MCP servers are unavailable"):
        await manager.manage(
            action="register",
            name="local-process",
            transport="stdio",
            command="python3",
            refresh=False,
        )


def test_stateless_oauth_code_uses_state_backend(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch, oauth_admin_pin="correct-pin")
    oauth_module._CLIENTS.clear()
    oauth_module._CODES.clear()
    app = Starlette(
        routes=[
            Route("/oauth/register", oauth_module.oauth_register, methods=["POST"]),
            Route("/oauth/authorize", oauth_module.oauth_authorize_post, methods=["POST"]),
            Route("/oauth/token", oauth_module.oauth_token, methods=["POST"]),
        ]
    )
    client = TestClient(app, base_url="https://controller.test")
    redirect = "https://client.test/callback"
    registered = client.post(
        "/oauth/register",
        json={"client_name": "serverless test", "redirect_uris": [redirect]},
    )
    client_id = registered.json()["client_id"]
    verifier = "serverless-verifier"
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    authorized = client.post(
        "/oauth/authorize",
        data={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "pin": "correct-pin",
        },
        follow_redirects=False,
    )
    code = parse_qs(urlsplit(authorized.headers["location"]).query)["code"][0]
    assert get_state_store().read_bytes(oauth_module.OAUTH_CODE_STORE_FILE_NAME) is not None

    oauth_module._CODES.clear()
    token = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "redirect_uri": redirect,
            "code_verifier": verifier,
        },
    )

    assert token.status_code == 200
    assert token.json()["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_stateless_invite_and_worker_identity_survive_cold_start(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch)
    first = remote_module.RemoteManager()
    invite = await first.create_invite(name="worker-a", workdir="/srv/work")

    clear_memory_state()
    second = remote_module.RemoteManager()
    registered = await second.register_worker(
        {
            "invite": invite["code"],
            "name": "worker-a",
            "workdir": "/srv/work",
            "capabilities": ["transfer_stat"],
            "info": {"hostname": "worker-a"},
        }
    )
    assert registered["token"].startswith("lsmcp_wk_s_")

    clear_memory_state()
    third = remote_module.RemoteManager()
    resumed = await third.resume_worker(
        registered["token"],
        {
            "name": "worker-a",
            "workdir": "/srv/work",
            "capabilities": ["transfer_stat"],
            "info": {"hostname": "worker-a"},
        },
    )

    assert resumed["name"] == "worker-a"
    assert "worker-a" in third.workers
    assert not get_settings().state_dir.exists()


@pytest.mark.asyncio
async def test_stateless_managed_job_and_audit_stay_off_disk(tmp_path, monkeypatch):
    _configure_stateless(tmp_path, monkeypatch)
    kind = f"serverless-test-{tmp_path.name}"

    async def handler(context: jobs_module.ManagedJobContext, payload: dict[str, Any]):
        await context.log("working")
        await context.update_progress(phase="done")
        return {"value": payload["value"]}

    jobs_module.register_managed_job_handler(kind, handler)
    job = await jobs_module.start_managed_job(kind, {"value": 7})
    for _ in range(100):
        await asyncio.sleep(0.01)
        rows = await jobs_module.list_jobs()
        current = next(row for row in rows["jobs"] if row["job_id"] == job["job_id"])
        if current["status"] != "running":
            break

    tail = await jobs_module.tail_job(job["job_id"])
    audit_module.audit("serverless_test", value=7)
    audit_rows = audit_module.query_audit(search="serverless_test")

    assert current["status"] == "succeeded"
    assert current["result"] == {"value": 7}
    assert "working" in tail["output"]
    assert audit_rows["count"] >= 1
    assert get_state_store().read_bytes("jobs.json") is not None
    assert get_state_store().read_bytes("audit.jsonl") is not None
    assert not get_settings().state_dir.exists()


@pytest.mark.asyncio
async def test_direct_remote_transfer_bypasses_controller_data_path(tmp_path, monkeypatch):
    root = _configure_workspace(
        tmp_path,
        monkeypatch,
        remote_transfer_strategy="direct",
        remote_peer_transfer_enabled="true",
        remote_peer_transfer_bind_host="127.0.0.1",
        remote_peer_transfer_advertise_host="127.0.0.1",
    )
    source = root / "source.bin"
    destination = root / "destination.bin"
    payload = bytes(range(256)) * 64
    source.write_bytes(payload)
    calls: list[tuple[str, str]] = []

    async def transfer(machine: str, tool: str, args: dict[str, Any], timeout_s=None):
        del timeout_s
        calls.append((machine, tool))
        if tool == "transfer_stat":
            return transfer_stat(args["path"], args.get("sha256", True))
        if tool == "transfer_open_receiver":
            return open_peer_receiver(
                path=args["path"],
                overwrite=args.get("overwrite", True),
                expected_bytes=args["expected_bytes"],
                expected_sha256=args["expected_sha256"],
                bind_host=args["bind_host"],
                advertise_host=args["advertise_host"],
                port=args["port"],
                timeout_s=args["timeout_s"],
            )
        if tool == "transfer_put_url":
            return remote_module._worker_put_url(
                args["path"],
                args["url"],
                args["expected_bytes"],
                args["expected_sha256"],
                args.get("timeout_s"),
            )
        raise AssertionError(f"unexpected tool: {tool}")

    monkeypatch.setattr(tools, "_remote_transfer_data", transfer)
    result = await tools._copy_remote_file_to_remote(
        "source-worker", "source.bin", "destination-worker", "destination.bin", True
    )

    assert result["transport"] == "peer-direct"
    assert destination.read_bytes() == payload
    assert ("destination-worker", "transfer_open_receiver") in calls
    assert ("source-worker", "transfer_put_url") in calls
    assert all(tool not in {"transfer_read_chunk", "transfer_write_chunk"} for _, tool in calls)


@pytest.mark.asyncio
async def test_object_store_transfer_uses_presigned_urls_and_deletes_object(tmp_path, monkeypatch):
    _configure_workspace(
        tmp_path,
        monkeypatch,
        remote_transfer_strategy="object_store",
        remote_transfer_s3_bucket="transfer-bucket",
        remote_transfer_s3_prefix="lsm-test",
    )
    content = b"object-store-transfer"
    digest = hashlib.sha256(content).hexdigest()

    class FakeS3:
        def __init__(self) -> None:
            self.deleted: list[tuple[str, str]] = []
            self.presigned: list[tuple[str, str]] = []

        def generate_presigned_url(self, operation, *, Params, ExpiresIn, HttpMethod):
            del ExpiresIn
            self.presigned.append((operation, HttpMethod))
            return f"https://storage.test/{Params['Bucket']}/{Params['Key']}?op={operation}"

        def delete_object(self, *, Bucket, Key):
            self.deleted.append((Bucket, Key))

    fake_s3 = FakeS3()
    monkeypatch.setattr(tools, "_s3_transfer_client", lambda: fake_s3)
    calls: list[tuple[str, str, dict[str, Any]]] = []

    async def transfer(machine: str, tool: str, args: dict[str, Any], timeout_s=None):
        del timeout_s
        calls.append((machine, tool, args))
        if tool == "transfer_stat":
            return {"type": "file", "path": "source.bin", "size": len(content), "sha256": digest}
        if tool == "transfer_put_url":
            assert args["url"].startswith("https://storage.test/")
            return {"bytes": len(content), "sha256": digest}
        if tool == "transfer_get_url":
            assert args["url"].startswith("https://storage.test/")
            return {"path": "destination.bin", "bytes": len(content), "sha256": digest}
        raise AssertionError(f"unexpected tool: {tool}")

    monkeypatch.setattr(tools, "_remote_transfer_data", transfer)
    result = await tools._copy_remote_file_to_remote(
        "source-worker", "source.bin", "destination-worker", "destination.bin", True
    )

    assert result["transport"] == "s3-presigned"
    assert fake_s3.presigned == [("put_object", "PUT"), ("get_object", "GET")]
    assert len(fake_s3.deleted) == 1
    assert fake_s3.deleted[0][0] == "transfer-bucket"
    assert [tool for _, tool, _ in calls] == ["transfer_stat", "transfer_put_url", "transfer_get_url"]
