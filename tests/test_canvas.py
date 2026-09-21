from fastapi.testclient import TestClient

from app.api.routes import query as query_module
from app.canvas import apply_canvas_command, detect_canvas_command
from app.main import app


client = TestClient(app)


def _page(question: str, *, news: bool = False) -> dict:
    blocks = [
        {"id": "summary", "type": "summary", "data_ref": "summary", "span": "full", "variant": "featured"},
        {"id": "metrics", "type": "metric_grid", "data_ref": "metrics", "span": "full", "variant": "default"},
    ]
    if news:
        blocks.append({"id": "news", "type": "news_feed", "data_ref": "news", "span": "full", "variant": "default"})
    return {
        "query": question,
        "response_type": "financial_news" if news else "company_research",
        "title": "Apple research" if not news else "Apple news",
        "summary": "Original company summary." if not news else "New news summary.",
        "headline": None,
        "insights": [],
        "metrics": [{"name": "Market Cap", "value": "$3T"}] if not news else [],
        "companies": [],
        "news": [{"title": "Apple launches a product", "url": "https://example.com/apple"}] if news else [],
        "evidence": [],
        "sources": [],
        "charts": [],
        "presentation": {"layout": "news_digest" if news else "research_dashboard", "blocks": blocks},
        "tool_calls": [],
        "generated_at": "2026-09-14T00:00:00+00:00",
        "_tool_executions": [],
    }


def test_add_command_merges_only_requested_content() -> None:
    current = _page("Research Apple")
    incoming = _page("Bring up Apple news", news=True)
    merged, operations = apply_canvas_command(current, incoming, "add", {"news_feed"})

    assert merged["summary"] == "Original company summary."
    assert merged["metrics"] == current["metrics"]
    assert merged["news"][0]["title"] == "Apple launches a product"
    assert any(block["type"] == "news_feed" for block in merged["presentation"]["blocks"])
    assert operations[0]["operation"] == "add"


def test_remove_command_does_not_need_generated_content() -> None:
    current = _page("Research Apple", news=True)
    merged, operations = apply_canvas_command(current, None, "remove", {"news_feed"})

    assert merged["news"] == []
    assert all(block["type"] != "news_feed" for block in merged["presentation"]["blocks"])
    assert operations == [{"operation": "remove", "block_type": "news_feed", "block_id": "news"}]


def test_entity_only_add_is_recognized() -> None:
    command = detect_canvas_command("Could you bring up Tesla too?", True)
    assert command is not None
    assert command.action == "add"
    assert command.targets == set()
    assert command.entities == {"TSLA"}
    assert detect_canvas_command("Remove it", True) is None


def test_trailing_also_add_command_is_recognized() -> None:
    command = detect_canvas_command("Bring Tesla stocks also", True)

    assert command is not None
    assert command.action == "add"
    assert command.targets == set()
    assert command.entities == {"TSLA"}


def test_adding_second_stock_preserves_both_price_cards_and_summaries() -> None:
    current = _page("What is Apple's stock price?")
    current["headline"] = {"label": "AAPL Stock Price", "value": "$200", "change": "+1%"}
    current["summary"] = "Apple is trading at $200."
    current["presentation"]["blocks"].insert(
        0,
        {"id": "headline", "type": "headline", "data_ref": "headline", "span": "full", "variant": "price"},
    )
    incoming = _page("Bring up Tesla too")
    incoming["headline"] = {"label": "TSLA Stock Price", "value": "$365", "change": "+0.5%"}
    incoming["summary"] = "Tesla is trading at $365."
    incoming["presentation"]["blocks"].insert(
        0,
        {"id": "headline", "type": "headline", "data_ref": "headline", "span": "full", "variant": "price"},
    )

    command = detect_canvas_command("Bring Tesla stocks also", True)
    assert command is not None
    merged, operations = apply_canvas_command(
        current,
        incoming,
        command.action,
        command.targets,
        command.entities,
    )

    assert [item["label"] for item in merged["headlines"]] == [
        "AAPL Stock Price",
        "TSLA Stock Price",
    ]
    assert merged["headline"] is None
    assert "Apple is trading at $200." in merged["summary"]
    assert "Tesla is trading at $365." in merged["summary"]
    assert merged["title"] == "Stock Price Board"
    assert merged["presentation"]["blocks"][0]["type"] == "headline_grid"
    assert any(operation["block_type"] == "headline_grid" for operation in operations)


def test_query_persists_and_updates_canvas(monkeypatch) -> None:
    def answer(question: str, _context=None) -> dict:
        return _page(question, news="news" in question.casefold())

    monkeypatch.setattr(query_module, "answer_question", answer)
    first = client.post("/api/v1/query", json={"question": "Research Apple"}).json()
    second = client.post(
        "/api/v1/query",
        json={
            "question": "Also bring up the latest news on screen",
            "conversation_id": first["conversation_id"],
            "canvas_revision": first["canvas_revision"],
        },
    )

    assert second.status_code == 200
    updated = second.json()
    assert updated["canvas_id"] == first["canvas_id"]
    assert updated["canvas_revision"] == 2
    assert updated["canvas_mode"] == "patch"
    assert updated["summary"] == "Original company summary."
    assert updated["news"]

    canvas = client.get(f"/api/v1/conversations/{first['conversation_id']}/canvas").json()
    assert canvas["revision"] == 2
    assert canvas["response"]["news"] == updated["news"]

    conflict = client.post(
        "/api/v1/query",
        json={
            "question": "Refresh the news",
            "conversation_id": first["conversation_id"],
            "canvas_revision": 1,
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CANVAS_REVISION_CONFLICT"
