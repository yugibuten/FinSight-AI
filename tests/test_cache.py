from unittest.mock import Mock

from app.core.cache import TTLCache, response_cache
from app.orchestrator import _execute


def test_ttl_cache_returns_a_copy_and_expires(monkeypatch) -> None:
    clock = iter([100.0, 101.0, 106.0])
    monkeypatch.setattr("app.core.cache.time.monotonic", lambda: next(clock))
    cache = TTLCache("test")
    original = {"items": [1]}
    cache.set("key", original, ttl_seconds=5)

    hit, cached = cache.get("key")
    assert hit is True
    cached["items"].append(2)
    assert original == {"items": [1]}

    hit, cached = cache.get("key")
    assert hit is False
    assert cached is None


def test_tool_cache_avoids_second_provider_call() -> None:
    provider = Mock(return_value={"success": True, "ticker": "AAPL", "price": 100})
    first = _execute("get_stock_price", {"ticker": "aapl"}, provider)
    second = _execute("get_stock_price", {"ticker": "AAPL"}, provider)

    assert first == second
    assert provider.call_count == 1


def test_failed_tool_results_are_not_cached() -> None:
    provider = Mock(return_value={"success": False, "error": "unavailable"})
    _execute("get_stock_price", {"ticker": "AAPL"}, provider)
    _execute("get_stock_price", {"ticker": "AAPL"}, provider)
    assert provider.call_count == 2


def test_response_cache_is_empty_between_tests() -> None:
    assert response_cache.get("missing") == (False, None)
