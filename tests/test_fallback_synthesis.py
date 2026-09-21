from app.models import FinSightSynthesis
from app.orchestrator import _build_fallback_synthesis, _enrich_synthesis_from_tools


def test_market_fallback_uses_successful_tool_data() -> None:
    calls = [
        {
            "name": "get_market_overview",
            "result": {
                "success": True,
                "region": "INDIA",
                "indices": [
                    {
                        "success": True,
                        "name": "NIFTY 50",
                        "ticker": "^NSEI",
                        "price": 25000,
                        "currency": "INR",
                        "change_percent": 1.25,
                    },
                    {
                        "success": True,
                        "name": "SENSEX",
                        "ticker": "^BSESN",
                        "price": 81000,
                        "currency": "INR",
                        "change_percent": -0.5,
                    },
                ],
            },
        }
    ]
    synthesis = _build_fallback_synthesis("How are Indian markets?", calls)
    assert synthesis.response_type == "market_overview"
    assert synthesis.metrics[0].change == "+1.25%"
    assert synthesis.metrics[1].change == "-0.50%"
    assert "1 advanced and 1 declined" in synthesis.direct_answer
    assert synthesis.summary != synthesis.direct_answer
    assert "temporarily unavailable" in synthesis.insights[0]


def test_price_fallback_is_grounded() -> None:
    calls = [
        {
            "name": "get_stock_price",
            "result": {
                "success": True,
                "ticker": "AAPL",
                "price": 231.45,
                "currency": "USD",
                "change_percent": 1.01,
                "as_of": "2026-09-13",
            },
        }
    ]
    synthesis = _build_fallback_synthesis("Apple price?", calls)
    assert synthesis.response_type == "stock_price"
    assert synthesis.headline is not None
    assert synthesis.headline.value == "231.45 USD"
    assert synthesis.headline.change == "+1.01%"
    assert "231.45 USD" in synthesis.direct_answer
    assert synthesis.summary != synthesis.direct_answer


def test_comparison_company_cards_are_enriched_from_tool_prices() -> None:
    synthesis = FinSightSynthesis(
        response_type="stock_comparison",
        title="Comparison",
        direct_answer="Apple led the comparison.",
        summary="Compare the supporting evidence.",
        companies=[
            {"ticker": "AAPL", "name": "Apple Inc."},
            {"ticker": "TSLA", "name": "Tesla Inc."},
        ],
    )
    calls = [
        {
            "name": "compare_stocks",
            "result": {
                "success": True,
                "stocks": [
                    {"success": True, "ticker": "AAPL", "end_price": 231.45, "currency": "USD", "change_percent": 12.5},
                    {"success": True, "ticker": "TSLA", "end_price": 365.44, "currency": "USD", "change_percent": -4.25},
                ],
            },
        }
    ]

    enriched = _enrich_synthesis_from_tools(synthesis, calls)

    assert enriched.companies[0].price == "231.45"
    assert enriched.companies[0].currency == "USD"
    assert enriched.companies[0].change == "+12.50%"
    assert enriched.companies[1].price == "365.44"
    assert enriched.companies[1].change == "-4.25%"
