import copy
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any

from app.core.config import settings


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


class RedisBackedTTLCache(TTLCache):
    """Shared Redis cache with a local fallback when Redis is unavailable."""

    def __init__(self, name: str, redis_url: str, max_entries: int = 500) -> None:
        super().__init__(name, max_entries)
        self._redis_url = redis_url
        self._redis = None

    def _client(self):
        if self._redis is None:
            from redis import Redis

            self._redis = Redis.from_url(
                self._redis_url, decode_responses=True, socket_connect_timeout=1
            )
        return self._redis

    def get(self, key: str) -> tuple[bool, Any]:
        try:
            raw = self._client().get(f"finsight:{self.name}:{key}")
            if raw is not None:
                self._log("cache.hit", key, backend="redis")
                return True, json.loads(raw)
        except Exception as exc:
            logger.warning(
                "cache.redis_unavailable",
                extra={"fields": {"cache": self.name, "error": type(exc).__name__}},
            )
        return super().get(key)

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        super().set(key, value, ttl_seconds)
        if ttl_seconds <= 0:
            return
        try:
            self._client().setex(
                f"finsight:{self.name}:{key}", int(max(1, ttl_seconds)), json.dumps(value)
            )
        except Exception as exc:
            logger.warning(
                "cache.redis_unavailable",
                extra={"fields": {"cache": self.name, "error": type(exc).__name__}},
            )


def cache_key(namespace: str, arguments: dict[str, Any]) -> str:
    return f"{namespace}:{json.dumps(arguments, sort_keys=True, separators=(',', ':'))}"


def _cache(name: str, max_entries: int) -> TTLCache:
    if settings.redis_url is not None:
        return RedisBackedTTLCache(
            name, settings.redis_url.get_secret_value(), max_entries=max_entries
        )
    return TTLCache(name, max_entries=max_entries)


tool_cache = _cache("tools", max_entries=1_000)
response_cache = _cache("responses", max_entries=250)
