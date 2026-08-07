from __future__ import annotations

import time
from pathlib import Path

import pytest

from local_shell_mcp import browser_sessions
from local_shell_mcp.browser_sessions import BrowserSessionManager, get_browser_session_manager
from local_shell_mcp.settings import get_settings


@pytest.fixture(autouse=True)
def _settings(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_SHELL_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("LOCAL_SHELL_MCP_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setenv("LOCAL_SHELL_MCP_AUTH_MODE", "none")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _pages(tmp_path: Path) -> tuple[str, str]:
    second = tmp_path / "second.html"
    second.write_text(
        "<html><head><title>Second</title></head><body><p>second page</p></body></html>",
        encoding="utf-8",
    )
    first = tmp_path / "index.html"
    first.write_text(
        f"""
<html>
<head><title>Browser Test</title></head>
<body>
  <button id="button" onclick="document.querySelector('#status').textContent='clicked'">Click me</button>
  <input id="input" placeholder="type here">
  <select id="select"><option value="a">A</option><option value="b">B</option></select>
  <input id="check" type="checkbox">
  <a id="link" href="{second.as_uri()}">Second page</a>
  <div id="status">ready</div>
  <img src="missing.png">
  <script>
    console.error('console-boom');
    setTimeout(() => {{ throw new Error('page-boom'); }}, 0);
  </script>
</body>
</html>
""".strip(),
        encoding="utf-8",
    )
    return first.as_uri(), second.as_uri()


@pytest.mark.asyncio
async def test_browser_session_snapshot_refs_actions_and_storage_state(tmp_path):
    first_url, second_url = _pages(tmp_path)
    manager = BrowserSessionManager(tmp_path / ".state")

    started = await manager.manage(action="start", url=first_url, width=900, height=700)
    session_id = started["session_id"]
    page_id = started["current_page_id"]
    assert started["browser"] == "chromium"
    assert started["pages"][0]["title"] == "Browser Test"

    await manager.act(session_id, [{"action": "wait", "ms": 30}], page_id=page_id)
    snapshot = await manager.snapshot(
        session_id, page_id=page_id, screenshot=True, max_text_chars=12, max_elements=50
    )
    assert snapshot["text_truncated"] is True
    assert Path(snapshot["screenshot_path"]).is_file()
    assert [row["ref"] for row in snapshot["interactive_elements"][:5]] == [
        "e1",
        "e2",
        "e3",
        "e4",
        "e5",
    ]
    assert any(item["kind"] == "console" for item in snapshot["errors"])
    assert any(item["kind"] in {"pageerror", "requestfailed"} for item in snapshot["errors"])

    acted = await manager.act(
        session_id,
        [
            {"action": "fill", "target": "e2", "value": "hello"},
            {"action": "press", "target": "#input", "key": "End"},
            {"action": "type", "target": "#input", "value": "!"},
            {"action": "select", "target": "#select", "value": "b"},
            {"action": "check", "target": "#check"},
            {"action": "uncheck", "target": "#check"},
            {"action": "hover", "target": "#button"},
            {"action": "click", "target": "e1"},
            {"action": "wait_for_text", "text": "clicked"},
            {"action": "wait", "ms": 1},
        ],
        page_id=page_id,
    )
    assert acted["page_id"] == page_id
    assert acted["results"][0]["target"] == "e2"

    state = await manager._get_session(session_id)
    original_page = state.pages[page_id].page
    assert await original_page.locator("#input").input_value() == "hello!"
    assert await original_page.locator("#select").input_value() == "b"
    assert await original_page.locator("#check").is_checked() is False
    assert await original_page.locator("#status").inner_text() == "clicked"

    new_page = await manager.act(
        session_id,
        [
            {"action": "new_page", "url": second_url},
            {"action": "wait_for_url", "url": second_url},
        ],
    )
    second_page_id = new_page["page_id"]
    assert second_page_id != page_id
    assert new_page["title"] == "Second"
    closed_page = await manager.act(
        session_id, [{"action": "close_page"}], page_id=second_page_id
    )
    assert closed_page["page_id"] == page_id

    navigated = await manager.act(
        session_id,
        [
            {"action": "navigate", "url": second_url, "wait_until": "load"},
            {"action": "wait_for_url", "url": second_url},
        ],
        page_id=page_id,
    )
    assert navigated["title"] == "Second"
    no_text = await manager.snapshot(
        session_id,
        page_id=page_id,
        include_text=False,
        screenshot=False,
        full_page=True,
        max_elements=1,
    )
    assert no_text["text"] is None
    assert no_text["screenshot_path"] is None

    storage_path = "browser-state.json"
    closed = await manager.manage(
        action="close", session_id=session_id, save_storage_state_path=storage_path
    )
    assert closed["closed"] is True
    assert (tmp_path / storage_path).is_file()

    restored = await manager.manage(
        action="start", url=first_url, storage_state_path=storage_path
    )
    assert restored["pages"][0]["title"] == "Browser Test"
    await manager.close(restored["session_id"])


@pytest.mark.asyncio
async def test_profiles_lists_cleanup_limits_and_singleton(tmp_path, monkeypatch):
    first_url, _ = _pages(tmp_path)
    manager = BrowserSessionManager(tmp_path / ".state")

    profile = await manager.start(url=first_url, profile_id="profile-1")
    assert profile["profile_id"] == "profile-1"
    assert (tmp_path / ".state" / "browser-profiles" / "profile-1").is_dir()
    listed = await manager.manage(action="list")
    assert [item["session_id"] for item in listed["sessions"]] == [profile["session_id"]]

    same_a = get_browser_session_manager(tmp_path / ".singleton")
    same_b = get_browser_session_manager(tmp_path / ".singleton")
    assert same_a is same_b

    state = await manager._get_session(profile["session_id"])
    state.last_used_at = time.time() - browser_sessions._IDLE_TIMEOUT_S - 1
    assert (await manager.manage(action="list"))["sessions"] == []

    monkeypatch.setattr(browser_sessions, "_MAX_SESSIONS", 1)
    one = await manager.start(url=first_url)
    with pytest.raises(ValueError, match="at most 1 browser sessions"):
        await manager.start(url=first_url)
    cleanup = await manager.manage(action="cleanup")
    assert cleanup["closed"] == 1
    with pytest.raises(ValueError, match="unknown browser session"):
        await manager.close(one["session_id"])


@pytest.mark.asyncio
async def test_browser_validation_and_action_errors(tmp_path, monkeypatch):
    first_url, _ = _pages(tmp_path)
    manager = BrowserSessionManager(tmp_path / ".state")

    with pytest.raises(ValueError, match="browser must be"):
        await manager.start(browser="netscape")
    with pytest.raises(ValueError, match="invalid wait_until"):
        await manager.start(wait_until="later")
    with pytest.raises(ValueError, match="profile_id"):
        await manager.start(profile_id="bad profile")
    with pytest.raises(ValueError, match="cannot be combined"):
        await manager.start(profile_id="p", storage_state_path="state.json")
    with pytest.raises(ValueError, match="action must be"):
        await manager.manage(action="wat")
    with pytest.raises(ValueError, match="session_id is required"):
        await manager.manage(action="close")
    with pytest.raises(ValueError, match="unknown browser session"):
        await manager.snapshot("missing")

    started = await manager.start(url=first_url)
    session_id = started["session_id"]
    with pytest.raises(ValueError, match="unknown browser page"):
        await manager.snapshot(session_id, page_id="missing")
    with pytest.raises(ValueError, match="at least one"):
        await manager.act(session_id, [])
    with pytest.raises(ValueError, match="at most"):
        await manager.act(session_id, [{"action": "wait"}] * (browser_sessions._MAX_ACTIONS + 1))
    with pytest.raises(ValueError, match=r"actions\[0\] must be an object"):
        await manager.act(session_id, ["bad"])
    with pytest.raises(ValueError, match=r"actions\[0\]\.action is required"):
        await manager.act(session_id, [{}])
    with pytest.raises(ValueError, match="requires url"):
        await manager.act(session_id, [{"action": "navigate"}])
    with pytest.raises(ValueError, match="invalid wait_until"):
        await manager.act(
            session_id,
            [{"action": "navigate", "url": first_url, "wait_until": "later"}],
        )
    with pytest.raises(ValueError, match="requires text"):
        await manager.act(session_id, [{"action": "wait_for_text"}])
    with pytest.raises(ValueError, match="requires url"):
        await manager.act(session_id, [{"action": "wait_for_url"}])
    with pytest.raises(ValueError, match="requires target"):
        await manager.act(session_id, [{"action": "click"}])
    with pytest.raises(ValueError, match="press requires key"):
        await manager.act(session_id, [{"action": "press", "target": "#input"}])
    with pytest.raises(ValueError, match="unsupported browser action"):
        await manager.act(session_id, [{"action": "dance", "target": "#input"}])

    await manager.act(
        session_id,
        [{"action": "select", "target": "#select", "value": ["a"]}],
        timeout_ms=999999,
    )
    await manager.close(session_id)


@pytest.mark.asyncio
async def test_start_failure_stops_playwright(tmp_path, monkeypatch):
    manager = BrowserSessionManager(tmp_path / ".state")
    stopped = {"value": False}

    class BrokenBrowserType:
        async def launch(self, **_kwargs):
            raise RuntimeError("launch failed")

    class FakePlaywright:
        chromium = BrokenBrowserType()
        firefox = BrokenBrowserType()
        webkit = BrokenBrowserType()

        async def stop(self):
            stopped["value"] = True

    class Starter:
        async def start(self):
            return FakePlaywright()

    monkeypatch.setattr("playwright.async_api.async_playwright", lambda: Starter())
    with pytest.raises(RuntimeError, match="launch failed"):
        await manager.start()
    assert stopped["value"] is True
