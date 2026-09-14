from app.orchestrator import _build_fallback_synthesis


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
    assert "1 advanced and 1 declined" in synthesis.summary
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
