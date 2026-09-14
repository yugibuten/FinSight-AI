from app.orchestrator import _build_charts


def test_history_chart_is_built_from_tool_prices() -> None:
    calls = [
        {
            "name": "get_stock_history",
            "result": {
                "success": True,
                "ticker": "AAPL",
                "period": "1mo",
                "currency": "USD",
                "prices": [
                    {"date": "2026-08-01", "close": 100.0},
                    {"date": "2026-09-01", "close": 110.0},
                ],
            },
        }
    ]
    chart = _build_charts(calls)[0]
    assert chart["type"] == "line"
    assert chart["unit"] == "USD"
    assert chart["series"][0]["data"][1] == {"x": "2026-09-01", "y": 110.0}


def test_comparison_chart_uses_normalized_returns() -> None:
    calls = [
        {
            "name": "compare_stocks",
            "result": {
                "success": True,
                "period": "1y",
                "normalized_series": [
                    {
                        "ticker": "AAPL",
                        "data": [
                            {"date": "2026-01-01", "value": 0.0},
                            {"date": "2026-02-01", "value": 8.5},
                        ],
                    },
                    {
                        "ticker": "MSFT",
                        "data": [
                            {"date": "2026-01-01", "value": 0.0},
                            {"date": "2026-02-01", "value": 4.0},
                        ],
                    },
                ],
            },
        }
    ]
    chart = _build_charts(calls)[0]
    assert chart["unit"] == "%"
    assert [series["name"] for series in chart["series"]] == ["AAPL", "MSFT"]


def test_no_chart_is_created_without_valid_data() -> None:
    assert _build_charts([{"name": "get_stock_history", "result": {"success": False}}]) == []
