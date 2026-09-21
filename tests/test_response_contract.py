from app.models import FinSightResponse
from app.orchestrator import _attribute_sources, _build_sources


def test_phase_three_response_supports_compact_price_layout() -> None:
    response = FinSightResponse(
        research_id="res_test",
        query="What is Apple's price?",
        response_type="stock_price",
        title="Apple stock price",
        summary="Apple closed higher.",
        headline={"label": "Apple", "value": "$231.45", "change": "+1.01%"},
        generated_at="2026-08-19T00:00:00+00:00",
    )
    assert response.headline is not None
    assert response.headline.change == "+1.01%"
    assert response.news == []


def test_sources_are_built_from_actual_tool_evidence() -> None:
    calls = [
        {
            "name": "get_stock_price",
            "arguments": {"ticker": "AAPL"},
            "result": {"success": True, "ticker": "AAPL", "price": 231.45},
        },
        {
            "name": "get_financial_news",
            "arguments": {"query": "Apple"},
            "result": {
                "success": True,
                "articles": [
                    {
                        "title": "Apple report",
                        "publisher": "Example News",
                        "url": "https://example.com/apple",
                    }
                ],
            },
        },
    ]
    sources = _build_sources(calls, "2026-08-19T00:00:00+00:00")
    assert sources[0]["url"] == "https://finance.yahoo.com/quote/AAPL"
    assert sources[0]["id"] == "src_1"
    assert sources[1]["provider"] == "Example News"


def test_claims_receive_deterministic_source_ids() -> None:
    synthesis = {
        "headline": {"label": "AAPL", "value": "$100"},
        "metrics": [{"name": "Return", "value": "5%", "ticker": "AAPL"}],
        "evidence": [{"claim": "Price rose", "metric": "Return", "value": "5%"}],
        "news": [{"title": "Apple report", "url": "https://example.com/apple"}],
    }
    sources = [
        {"id": "src_1", "title": "AAPL market data", "url": "https://finance.yahoo.com/quote/AAPL"},
        {"id": "src_2", "title": "Apple report", "url": "https://example.com/apple"},
    ]
    attributed = _attribute_sources(synthesis, sources)
    assert attributed["headline"]["source_ids"] == ["src_1"]
    assert attributed["metrics"][0]["source_ids"] == ["src_1"]
    assert attributed["evidence"][0]["source_ids"] == ["src_1", "src_2"]
    assert attributed["news"][0]["source_ids"] == ["src_2"]
