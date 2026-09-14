from fastapi.testclient import TestClient

import app.main as api_module
from app.api.routes import query as query_module
from app.core.exceptions import ProviderRateLimitError


client = TestClient(api_module.app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api_version": "v1"}
    assert response.headers["x-request-id"].startswith("req_")


def test_caller_request_id_is_preserved() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "test-request-1"})
    assert response.headers["x-request-id"] == "test-request-1"


def test_local_frontend_cors() -> None:
    response = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_query_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        query_module,
        "answer_question",
        lambda question: {
            "query": question,
            "response_type": "stock_price",
            "title": "Apple stock price",
            "summary": "Apple is trading higher.",
            "headline": {
                "label": "Apple",
                "value": "$231.45",
                "change": "+1.01%",
                "context": "Latest trading session",
            },
            "insights": [],
            "metrics": [],
            "companies": [],
            "news": [],
            "evidence": [],
            "sources": [],
            "tool_calls": [
                {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
            ],
            "generated_at": "2026-08-19T00:00:00+00:00",
        },
    )
    response = client.post("/api/v1/query", json={"question": "Apple price?"})
    assert response.status_code == 200
    assert response.json()["response_type"] == "stock_price"
    assert response.json()["headline"]["value"] == "$231.45"
    assert response.json()["tool_calls"][0]["name"] == "get_stock_price"


def test_repeated_query_uses_response_cache(monkeypatch) -> None:
    calls = 0

    def answer(question: str) -> dict:
        nonlocal calls
        calls += 1
        return {
            "query": question,
            "response_type": "general_explanation",
            "title": "P/E ratio",
            "summary": "A valuation ratio.",
            "headline": None,
            "insights": [],
            "metrics": [],
            "companies": [],
            "news": [],
            "evidence": [],
            "sources": [],
            "tool_calls": [],
            "generated_at": "2026-09-13T00:00:00+00:00",
        }

    monkeypatch.setattr(query_module, "answer_question", answer)
    first = client.post("/api/v1/query", json={"question": "Explain a P/E ratio"})
    second = client.post("/api/v1/query", json={"question": "  EXPLAIN  a p/e RATIO "})
    assert first.status_code == second.status_code == 200
    assert calls == 1


def test_query_rejects_blank_question() -> None:
    response = client.post("/api/v1/query", json={"question": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert response.json()["error"]["request_id"].startswith("req_")


def test_query_hides_internal_errors(monkeypatch) -> None:
    def fail(_: str) -> dict:
        raise RuntimeError("secret provider detail")

    monkeypatch.setattr(query_module, "answer_question", fail)
    response = client.post("/api/v1/query", json={"question": "Apple price?"})
    assert response.status_code == 502
    assert "secret provider detail" not in response.text
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


def test_provider_rate_limit_has_stable_error(monkeypatch) -> None:
    def rate_limited(_: str) -> dict:
        raise ProviderRateLimitError()

    monkeypatch.setattr(query_module, "answer_question", rate_limited)
    response = client.post("/api/v1/query", json={"question": "Apple price?"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "PROVIDER_RATE_LIMITED"
    assert response.json()["error"]["retryable"] is True


def test_request_body_size_guard() -> None:
    response = client.post(
        "/api/v1/query",
        content=b"x" * 17_000,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_legacy_routes_work_but_are_hidden_from_schema() -> None:
    assert client.get("/health").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/query" in paths
    assert "/health" not in paths
    assert "/query" not in paths
