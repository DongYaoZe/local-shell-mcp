from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from local_shell_mcp import chat_dispatch_bridge, tools


class FakeStore:
    jobs = {}
    cancelled = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def enqueue(self, **kwargs):
        job = SimpleNamespace(
            dispatch_id="chat_1",
            state="QUEUED",
            prompt_text=kwargs["prompt"],
            kwargs=kwargs,
        )
        self.jobs[job.dispatch_id] = job
        return job

    def cancel(self, dispatch_id):
        self.cancelled.append(dispatch_id)
        job = self.jobs.setdefault(
            dispatch_id,
            SimpleNamespace(dispatch_id=dispatch_id, state="CANCELLED", prompt_text=""),
        )
        job.state = "CANCELLED"
        return job


class FakeBackend:
    ChatDispatchStore = FakeStore
    TERMINAL_JOB_STATES = {"ACKNOWLEDGED", "FAILED", "CANCELLED"}
    ensure_calls = []
    status_calls = []

    @staticmethod
    def job_payload(job):
        return {"dispatch_id": job.dispatch_id, "state": job.state}

    @classmethod
    def ensure_chat_dispatch_worker(cls, **kwargs):
        cls.ensure_calls.append(kwargs)
        return {"started": True, "pid": 123}

    @classmethod
    def chat_dispatch_status(cls, **kwargs):
        cls.status_calls.append(kwargs)
        return {"jobs": [], "pages": [], "pending": 0, "lease": None}


class ChatDispatchBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "lws"
        self.root.mkdir()
        FakeStore.jobs = {}
        FakeStore.cancelled = []
        FakeBackend.ensure_calls = []
        FakeBackend.status_calls = []
        self.load_patch = patch.object(
            chat_dispatch_bridge,
            "_load_backend",
            return_value=(self.root, FakeBackend),
        )
        self.load_patch.start()
        self.settings = SimpleNamespace(
            workspace_root=Path(self.tmp.name),
            chat_dispatch_lws_repo=None,
            chat_dispatch_max_windows=4,
            chat_dispatch_idle_close_s=90,
        )

    def tearDown(self):
        self.load_patch.stop()
        self.tmp.cleanup()

    def test_enqueue_forwards_durable_identity_and_starts_worker(self):
        result = chat_dispatch_bridge.manage_chat_dispatch(
            self.settings,
            action="enqueue",
            prompt="do the child work",
            conversation_key="child-a",
            project_url="https://chatgpt.com/g/project",
            idempotency_key="request-42",
            max_windows=3,
            idle_close_s=45,
        )
        self.assertEqual(result["dispatch"]["dispatch_id"], "chat_1")
        job = FakeStore.jobs["chat_1"]
        self.assertEqual(job.kwargs["dispatch_key"], "request-42")
        self.assertEqual(job.kwargs["conversation_key"], "child-a")
        self.assertEqual(job.kwargs["max_windows"], 3)
        self.assertEqual(job.kwargs["idle_close_s"], 45)
        self.assertEqual(FakeBackend.ensure_calls[-1]["repo_root"], self.root)

    def test_enqueue_requires_idempotency_key_before_loading_backend(self):
        with self.assertRaisesRegex(ValueError, "idempotency_key is required"):
            chat_dispatch_bridge.manage_chat_dispatch(
                self.settings,
                action="enqueue",
                prompt="do work",
                conversation_url="https://chatgpt.com/c/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            )

    def test_new_conversation_requires_stable_conversation_key(self):
        with self.assertRaisesRegex(ValueError, "conversation_key is required"):
            chat_dispatch_bridge.manage_chat_dispatch(
                self.settings,
                action="enqueue",
                prompt="do work",
                project_url="https://chatgpt.com/g/project",
                idempotency_key="request-1",
            )

    def test_enqueue_rejects_ambiguous_existing_and_new_targets(self):
        with self.assertRaisesRegex(ValueError, "not both"):
            chat_dispatch_bridge.manage_chat_dispatch(
                self.settings,
                action="enqueue",
                prompt="do work",
                conversation_key="child-a",
                conversation_url="https://chatgpt.com/c/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                project_url="https://chatgpt.com/g/project",
                idempotency_key="request-1",
            )

    def test_status_limit_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "limit must be between"):
            chat_dispatch_bridge.manage_chat_dispatch(
                self.settings, action="status", limit=501
            )

    def test_status_does_not_start_worker(self):
        result = chat_dispatch_bridge.manage_chat_dispatch(
            self.settings, action="status", dispatch_id="chat_1", limit=7
        )
        self.assertEqual(result["action"], "status")
        self.assertEqual(FakeBackend.ensure_calls, [])
        self.assertEqual(
            FakeBackend.status_calls[-1], {"dispatch_id": "chat_1", "limit": 7}
        )

    def test_cancel_is_followed_by_worker_ensure_for_page_cleanup(self):
        FakeStore.jobs["chat_1"] = SimpleNamespace(
            dispatch_id="chat_1", state="QUEUED", prompt_text="x"
        )
        result = chat_dispatch_bridge.manage_chat_dispatch(
            self.settings, action="cancel", dispatch_id="chat_1"
        )
        self.assertEqual(result["dispatch"]["state"], "CANCELLED")
        self.assertEqual(FakeStore.cancelled, ["chat_1"])
        self.assertEqual(len(FakeBackend.ensure_calls), 1)

    def test_prompt_is_redacted_from_tool_audit_arguments(self):
        safe = tools._safe_audit_call_arguments(
            "chat_dispatch",
            {"action": "enqueue", "prompt": "非常敏感的子任务提示", "conversation_key": "c"},
        )
        self.assertTrue(safe["prompt"].startswith("<redacted:"))
        self.assertNotIn("敏感", safe["prompt"])
        self.assertEqual(safe["conversation_key"], "c")

    def test_chat_dispatch_is_model_visible_with_open_world_mutation_annotations(self):
        async def listed():
            return {tool.name: tool for tool in await tools.build_mcp().list_tools()}

        visible = asyncio.run(listed())
        self.assertIn("chat_dispatch", visible)
        tool = visible["chat_dispatch"]
        self.assertTrue(tool.annotations.openWorldHint)
        self.assertFalse(tool.annotations.readOnlyHint)
        self.assertTrue(tool.annotations.destructiveHint)
        for name in (
            "action",
            "prompt",
            "conversation_key",
            "conversation_url",
            "project_url",
            "dispatch_id",
            "idempotency_key",
            "max_windows",
            "idle_close_s",
            "limit",
        ):
            self.assertIn(name, tool.inputSchema["properties"])


class ChatDispatchBackendContractTests(unittest.TestCase):
    def test_incompatible_backend_fails_with_missing_api_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module = SimpleNamespace(__file__=str(root / "src" / "lws" / "chat_dispatch.py"))
            old_cache = chat_dispatch_bridge._BACKEND_CACHE
            chat_dispatch_bridge._BACKEND_CACHE = None
            try:
                with (
                    patch.object(chat_dispatch_bridge, "_resolve_lws_repo", return_value=root),
                    patch.object(chat_dispatch_bridge.importlib, "import_module", return_value=module),
                    self.assertRaisesRegex(RuntimeError, "missing API: ChatDispatchStore"),
                ):
                    chat_dispatch_bridge._load_backend(SimpleNamespace())
            finally:
                chat_dispatch_bridge._BACKEND_CACHE = old_cache


if __name__ == "__main__":
    unittest.main()
