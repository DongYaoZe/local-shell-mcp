from pathlib import Path

path = Path("tests/test_live_workspace.py")
text = path.read_text()

old = 'started = manager.manage("direct", "user", action="start", objective="Cancelable task")'
new = 'started = manager.manage("direct", "local-mcp-client", action="start", objective="Cancelable task")'
if text.count(old) != 1:
    raise SystemExit(f"cancel fixture identity: expected one match, found {text.count(old)}")
text = text.replace(old, new, 1)

old = '''@pytest.mark.asyncio
async def test_completed_tool_result_survives_session_activity_write_failure(
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
    _, result = await mcp.call_tool(
        "write_file",
        {
            "path": "completed.txt",
            "content": "completed once",
            "session_run_id": run_id,
        },
    )
    assert result["ok"] is True
    assert (tmp_path / "completed.txt").read_text(encoding="utf-8") == "completed once"
'''
new = '''@pytest.mark.asyncio
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
            "write_file",
            {
                "path": "completed.txt",
                "content": "must not be written",
                "session_run_id": run_id,
            },
        )
    assert not (tmp_path / "completed.txt").exists()
'''
if text.count(old) != 1:
    raise SystemExit(f"fail-closed integration test: expected one match, found {text.count(old)}")
path.write_text(text.replace(old, new, 1))
