import copy
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any


logger = logging.getLogger("finsight.cache")


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """Small thread-safe, process-local TTL cache with bounded memory usage."""

    def __init__(self, name: str, max_entries: int = 500) -> None:
        self.name = name
        self.max_entries = max_entries
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> tuple[bool, Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._log("cache.miss", key)
                return False, None
            if entry.expires_at <= now:
                del self._entries[key]
                self._log("cache.expired", key)
                return False, None
            self._entries.move_to_end(key)
            value = copy.deepcopy(entry.value)
        self._log("cache.hit", key)
        return True, value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            return
        with self._lock:
            self._entries[key] = CacheEntry(
                value=copy.deepcopy(value),
                expires_at=time.monotonic() + ttl_seconds,
            )
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        self._log("cache.stored", key, ttl_seconds=ttl_seconds)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _log(self, event: str, key: str, **fields: Any) -> None:
        logger.info(
            event,
            extra={
                "fields": {
                    "cache": self.name,
                    # Log a short stable key preview, not the full user question.
                    "key": key[:80],
                    **fields,
                }
            },
        )


def cache_key(namespace: str, arguments: dict[str, Any]) -> str:
    return f"{namespace}:{json.dumps(arguments, sort_keys=True, separators=(',', ':'))}"


tool_cache = TTLCache("tools", max_entries=1_000)
response_cache = TTLCache("responses", max_entries=250)
