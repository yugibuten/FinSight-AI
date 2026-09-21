from unittest.mock import patch

import pandas as pd

from app.tools.stock_tool import (
    compare_stocks,
    get_stock_history,
    normalize_symbol,
    safe_number,
)


def test_normalize_symbol() -> None:
    assert normalize_symbol("  paytm.ns ") == "PAYTM.NS"


def test_safe_number() -> None:
    assert safe_number(1.23456) == 1.2346
    assert safe_number(float("nan")) is None


def test_history_rejects_unsupported_period() -> None:
    result = get_stock_history("AAPL", "7years")
    assert result["success"] is False
    assert result["error"] == "Unsupported period: 7years"


def test_compare_stocks_ranks_by_calculated_return() -> None:
    apple = {"success": True, "ticker": "AAPL", "change_percent": 12.0, "prices": []}
    microsoft = {"success": True, "ticker": "MSFT", "change_percent": 8.0, "prices": []}
    with patch(
        "app.tools.stock_tool.get_stock_history", side_effect=[apple, microsoft]
    ):
        result = compare_stocks(["aapl", "msft"], "1y")
    assert result["success"] is True
    assert result["best_performer"] == "AAPL"
    assert all("prices" not in stock for stock in result["stocks"])


def test_history_calculates_return_from_mocked_market_data() -> None:
    dates = pd.to_datetime(["2026-01-01", "2026-01-02"])
    frame = pd.DataFrame({"Close": [100.0, 110.0]}, index=dates)
    with patch("app.providers.yahoo.yf.Ticker") as ticker:
        ticker.return_value.history.return_value = frame
        result = get_stock_history("AAPL", "5d")
    assert result["change_percent"] == 10.0
    assert result["high"] == 110.0
    assert result["low"] == 100.0
