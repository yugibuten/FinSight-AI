import asyncio

from starlette.requests import Request

from app.api.routes import query as query_module
from app.schemas.query import QueryRequest


def test_component_stream_orders_response_and_blocks(monkeypatch) -> None:
    def answer(question: str) -> dict:
        return {
            "query": question,
            "response_type": "stock_price",
            "title": "Apple stock price",
            "direct_answer": "Apple is trading at $200.",
            "summary": "This is the latest available closing snapshot.",
            "headline": {"label": "AAPL", "value": "$200", "change": "+1%"},
            "insights": [],
            "metrics": [],
            "companies": [],
            "news": [],
            "evidence": [],
            "sources": [],
            "charts": [],
            "presentation": {
                "layout": "compact",
                "blocks": [
                    {"id": "answer", "type": "direct_answer", "data_ref": "direct_answer", "span": "full", "variant": "featured"},
                    {"id": "headline", "type": "headline", "data_ref": "headline", "span": "full", "variant": "price"},
                    {"id": "summary", "type": "summary", "data_ref": "summary", "span": "full", "variant": "featured"},
                ],
            },
            "tool_calls": [],
            "generated_at": "2026-09-16T00:00:00+00:00",
            "_tool_executions": [],
        }

    monkeypatch.setattr(query_module, "answer_question", answer)
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/query/stream", "headers": []})
    request.state.request_id = "req_stream_test"

    async def collect() -> str:
        response = await query_module.query_stream(
            QueryRequest(question="What is Apple's price?"), request
        )
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
        return "".join(chunks)

    body = asyncio.run(collect())

    assert body.index("event: status") < body.index("event: response_start")
    assert body.count("event: component") == 3
    assert body.index('"type": "direct_answer"') < body.index('"type": "headline"')
    assert body.index('"type": "headline"') < body.index('"type": "summary"')
    assert body.index("event: response_start") < body.index("event: complete")
