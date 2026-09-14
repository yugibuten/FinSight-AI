import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import query as query_module
from app.core.config import Settings
from app.core.middleware import RequestContextMiddleware, RequestGuardMiddleware


def test_query_timeout(monkeypatch) -> None:
    def slow_answer(_: str) -> dict:
        time.sleep(0.05)
        return {}

    monkeypatch.setattr(query_module, "answer_question", slow_answer)
    monkeypatch.setattr(query_module.settings, "query_timeout_seconds", 0.01)
    from app.main import app

    response = TestClient(app).post("/api/v1/query", json={"question": "A question"})
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "QUERY_TIMEOUT"


def test_in_memory_rate_limit() -> None:
    guarded_app = FastAPI()

    @guarded_app.post("/api/v1/query")
    def endpoint() -> dict[str, bool]:
        return {"ok": True}

    test_settings = Settings(rate_limit_requests=1, rate_limit_window_seconds=60)
    guarded_app.add_middleware(RequestGuardMiddleware, settings=test_settings)
    guarded_app.add_middleware(RequestContextMiddleware)
    guarded_client = TestClient(guarded_app)

    assert guarded_client.post("/api/v1/query", json={}).status_code == 200
    response = guarded_client.post("/api/v1/query", json={})
    assert response.status_code == 429
    assert response.headers["retry-after"]
    assert response.json()["error"]["code"] == "RATE_LIMITED"
