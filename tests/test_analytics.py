import pandas as pd

from app.analytics import calculate_price_analytics


def test_price_analytics_are_deterministic() -> None:
    dates = pd.date_range("2025-01-01", periods=252, freq="B")
    closes = pd.Series([100 + index * 0.2 for index in range(252)], index=dates)
    analytics = calculate_price_analytics(closes)

    assert analytics["observations"] == 252
    assert analytics["cagr_percent"] is not None
    assert analytics["annualized_volatility_percent"] is not None
    assert analytics["maximum_drawdown_percent"] == 0.0
    assert analytics["sma_20"] == round(closes.tail(20).mean(), 4)
    assert analytics["sma_50"] == round(closes.tail(50).mean(), 4)


def test_drawdown_is_calculated_from_running_peak() -> None:
    dates = pd.date_range("2026-01-01", periods=4)
    closes = pd.Series([100.0, 120.0, 90.0, 105.0], index=dates)
    assert calculate_price_analytics(closes)["maximum_drawdown_percent"] == -25.0
