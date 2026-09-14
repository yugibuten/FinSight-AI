from fastapi.testclient import TestClient

from app.api.routes import query as query_module
from app.core.exceptions import ProviderRateLimitError
from app.main import app


client = TestClient(app)


def _result(question: str) -> dict:
    return {
        "query": question,
        "response_type": "stock_price",
        "title": "Apple stock price",
        "summary": "Apple has a latest available price.",
        "headline": {"label": "Apple", "value": "$100", "change": "+1%"},
        "insights": [],
        "metrics": [],
        "companies": [],
        "news": [],
        "evidence": [],
        "sources": [],
        "charts": [],
        "tool_calls": [{"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}],
        "generated_at": "2026-09-13T00:00:00+00:00",
        "_tool_executions": [
            {
                "name": "get_stock_price",
                "arguments": {"ticker": "AAPL"},
                "success": True,
                "cache_hit": False,
                "duration_ms": 12.5,
            }
        ],
    }


def test_successful_query_is_saved_and_can_be_deleted(monkeypatch) -> None:
    monkeypatch.setattr(query_module, "answer_question", _result)
    response = client.post("/api/v1/query", json={"question": "Apple price"})
    assert response.status_code == 200
    research_id = response.json()["research_id"]
    assert research_id.startswith("res_")

    history = client.get("/api/v1/research").json()
    assert history[0]["id"] == research_id
    assert history[0]["status"] == "completed"

    detail = client.get(f"/api/v1/research/{research_id}").json()
    assert detail["result"]["summary"] == "Apple has a latest available price."
    assert detail["tool_executions"][0]["tool_name"] == "get_stock_price"
    assert detail["tool_executions"][0]["duration_ms"] == 12.5

    assert client.delete(f"/api/v1/research/{research_id}").status_code == 204
    assert client.get(f"/api/v1/research/{research_id}").status_code == 404


def test_failed_query_is_saved(monkeypatch) -> None:
    def fail(_: str) -> dict:
        raise ProviderRateLimitError()

    monkeypatch.setattr(query_module, "answer_question", fail)
    response = client.post("/api/v1/query", json={"question": "A unique failed query"})
    assert response.status_code == 429

    history = client.get("/api/v1/research").json()
    assert history[0]["status"] == "failed"
    assert history[0]["error_code"] == "PROVIDER_RATE_LIMITED"


def test_response_cache_hit_creates_separate_history_record(monkeypatch) -> None:
    calls = 0

    def answer(question: str) -> dict:
        nonlocal calls
        calls += 1
        return _result(question)

    monkeypatch.setattr(query_module, "answer_question", answer)
    first = client.post("/api/v1/query", json={"question": "Unique cached price"}).json()
    second = client.post("/api/v1/query", json={"question": "unique CACHED price"}).json()
    assert calls == 1
    assert first["research_id"] != second["research_id"]

    history = client.get("/api/v1/research").json()
    assert len(history) == 2
    assert any(item["response_cache_hit"] for item in history)
