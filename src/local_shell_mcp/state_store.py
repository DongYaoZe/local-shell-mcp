from __future__ import annotations

import contextlib
import json
import threading
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

from .settings import get_settings


class StateStore(Protocol):
    def read_bytes(self, key: str) -> bytes | None: ...

    def write_bytes(self, key: str, value: bytes) -> None: ...

    def delete(self, key: str) -> None: ...

    def list_keys(self, prefix: str = "") -> list[str]: ...

    def lock(self, key: str) -> contextlib.AbstractContextManager[None]: ...


class FileStateStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = self.root / key
        resolved_root = self.root.resolve()
        resolved = path.resolve()
        if resolved != resolved_root and resolved_root not in resolved.parents:
            raise ValueError(f"state key escapes state directory: {key}")
        return path

    def read_bytes(self, key: str) -> bytes | None:
        path = self._path(key)
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None

    def write_bytes(self, key: str, value: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_bytes(value)
            with contextlib.suppress(OSError):
                temporary.chmod(0o600)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def list_keys(self, prefix: str = "") -> list[str]:
        if not self.root.exists():
            return []
        keys: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            key = path.relative_to(self.root).as_posix()
            if key.startswith(prefix):
                keys.append(key)
        return sorted(keys)

    @contextlib.contextmanager
    def lock(self, key: str) -> Iterator[None]:
        del key
        yield


_MEMORY_VALUES: dict[str, bytes] = {}
_MEMORY_LOCKS: dict[str, threading.RLock] = {}
_MEMORY_GUARD = threading.RLock()


class MemoryStateStore:
    def __init__(self, namespace: str = "local-shell-mcp") -> None:
        self._namespace = namespace.strip(":") or "local-shell-mcp"

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    def _lock_for(self, key: str) -> threading.RLock:
        key = self._key(key)
        with _MEMORY_GUARD:
            return _MEMORY_LOCKS.setdefault(key, threading.RLock())

    def read_bytes(self, key: str) -> bytes | None:
        namespaced = self._key(key)
        with self._lock_for(key):
            value = _MEMORY_VALUES.get(namespaced)
            return None if value is None else bytes(value)

    def write_bytes(self, key: str, value: bytes) -> None:
        namespaced = self._key(key)
        with self._lock_for(key):
            _MEMORY_VALUES[namespaced] = bytes(value)

    def delete(self, key: str) -> None:
        namespaced = self._key(key)
        with self._lock_for(key):
            _MEMORY_VALUES.pop(namespaced, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        namespace_prefix = f"{self._namespace}:"
        with _MEMORY_GUARD:
            keys = [
                key.removeprefix(namespace_prefix)
                for key in _MEMORY_VALUES
                if key.startswith(namespace_prefix)
                and key.removeprefix(namespace_prefix).startswith(prefix)
            ]
        return sorted(keys)

    @contextlib.contextmanager
    def lock(self, key: str) -> Iterator[None]:
        with self._lock_for(key):
            yield


class RedisStateStore:
    def __init__(self, url: str, prefix: str) -> None:
        try:
            import redis
        except ImportError as exc:  # pragma: no cover - depends on optional extra.
            raise RuntimeError(
                "Redis state backend requires the 'redis' package; install local-shell-mcp[redis]"
            ) from exc
        self._client = redis.Redis.from_url(url)
        self._prefix = prefix.strip(":") or "local-shell-mcp"

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def read_bytes(self, key: str) -> bytes | None:
        value = self._client.get(self._key(key))
        return None if value is None else bytes(value)

    def write_bytes(self, key: str, value: bytes) -> None:
        self._client.set(self._key(key), value)

    def delete(self, key: str) -> None:
        self._client.delete(self._key(key))

    def list_keys(self, prefix: str = "") -> list[str]:
        full_prefix = self._key(prefix)
        namespace_prefix = f"{self._prefix}:"
        keys: list[str] = []
        for raw in self._client.scan_iter(match=full_prefix + "*"):
            decoded = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            if decoded.startswith(namespace_prefix):
                keys.append(decoded.removeprefix(namespace_prefix))
        return sorted(keys)

    @contextlib.contextmanager
    def lock(self, key: str) -> Iterator[None]:
        lock = self._client.lock(self._key(f"locks:{key}"), timeout=30, blocking_timeout=5)
        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise TimeoutError(f"timed out acquiring state lock: {key}")
        try:
            yield
        finally:
            with contextlib.suppress(Exception):
                lock.release()


_STORE_CACHE: tuple[tuple[str, str | None, str, str], StateStore] | None = None
_STORE_CACHE_LOCK = threading.Lock()


def get_state_store() -> StateStore:
    global _STORE_CACHE
    settings = get_settings()
    signature = (
        settings.state_backend,
        settings.state_backend_url,
        settings.state_backend_prefix,
        str(settings.state_dir),
    )
    with _STORE_CACHE_LOCK:
        if _STORE_CACHE is not None and _STORE_CACHE[0] == signature:
            return _STORE_CACHE[1]
        if settings.state_backend == "file":
            store: StateStore = FileStateStore(settings.state_dir)
        elif settings.state_backend == "memory":
            store = MemoryStateStore(settings.state_backend_prefix)
        elif settings.state_backend == "redis":
            if not settings.state_backend_url:
                raise ValueError("state_backend_url is required when state_backend=redis")
            store = RedisStateStore(settings.state_backend_url, settings.state_backend_prefix)
        else:  # pragma: no cover - settings validation protects this branch.
            raise ValueError(f"unsupported state backend: {settings.state_backend}")
        _STORE_CACHE = (signature, store)
        return store


def read_json(key: str, default: Any = None) -> Any:
    raw = get_state_store().read_bytes(key)
    if raw is None:
        return default
    return json.loads(raw.decode("utf-8"))


def write_json(key: str, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    get_state_store().write_bytes(key, payload)


def delete_state(key: str) -> None:
    get_state_store().delete(key)


@contextlib.contextmanager
def state_lock(key: str) -> Iterator[None]:
    with get_state_store().lock(key):
        yield


def clear_memory_state() -> None:
    """Clear process-local state. Intended for tests and explicit ephemeral resets."""
    with _MEMORY_GUARD:
        _MEMORY_VALUES.clear()
        _MEMORY_LOCKS.clear()
