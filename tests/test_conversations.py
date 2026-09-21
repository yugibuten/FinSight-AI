from fastapi.testclient import TestClient

from app.api.routes import query as query_module
from app.main import app


client = TestClient(app)


def _result(question: str) -> dict:
    return {
        "query": question,
        "response_type": "stock_price",
        "title": "Stock research",
        "summary": f"Grounded answer for {question}",
        "headline": None,
        "insights": [],
        "metrics": [],
        "companies": [{"ticker": "AAPL", "name": "Apple"}],
        "news": [],
        "evidence": [],
        "sources": [],
        "charts": [],
        "tool_calls": [{"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}],
        "generated_at": "2026-09-14T00:00:00+00:00",
        "_tool_executions": [],
    }


def test_query_creates_conversation_and_follow_up_receives_context(monkeypatch) -> None:
    received_contexts: list[list[dict] | None] = []

    def answer(question: str, context: list[dict] | None = None) -> dict:
        received_contexts.append(context)
        return _result(question)

    monkeypatch.setattr(query_module, "answer_question", answer)
    first = client.post("/api/v1/query", json={"question": "What is Apple's price?"})
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/v1/query",
        json={"question": "Compare it with Microsoft", "conversation_id": conversation_id},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
    assert received_contexts[0] is None
    assert received_contexts[1][0]["question"] == "What is Apple's price?"

    detail = client.get(f"/api/v1/conversations/{conversation_id}").json()
    assert detail["turn_count"] == 2
    assert [turn["turn_index"] for turn in detail["turns"]] == [1, 2]


def test_standalone_turn_does_not_receive_old_context(monkeypatch) -> None:
    received_contexts: list[list[dict] | None] = []

    def answer(question: str, context: list[dict] | None = None) -> dict:
        received_contexts.append(context)
        return _result(question)

    monkeypatch.setattr(query_module, "answer_question", answer)
    first = client.post("/api/v1/query", json={"question": "What is Apple's price?"}).json()
    client.post(
        "/api/v1/query",
        json={
            "question": "What is the price of MSFT?",
            "conversation_id": first["conversation_id"],
        },
    )

    assert received_contexts == [None, None]


def test_conversation_crud_and_unknown_conversation(monkeypatch) -> None:
    created = client.post("/api/v1/conversations", json={"title": "Semiconductors"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]
    assert created.json()["turn_count"] == 0
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 200
    assert any(item["id"] == conversation_id for item in client.get("/api/v1/conversations").json())

    assert client.delete(f"/api/v1/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404

    missing = client.post(
        "/api/v1/query",
        json={"question": "What about it?", "conversation_id": "con_" + "0" * 32},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"
