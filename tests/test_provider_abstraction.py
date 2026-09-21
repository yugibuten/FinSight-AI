import pandas as pd

from app.providers.registry import get_market_data_provider, set_market_data_provider
from app.tools.stock_tool import get_stock_price


class _Ticker:
    fast_info = {"currency": "USD"}

    def history(self, **_kwargs):
        dates = pd.to_datetime(["2026-09-10", "2026-09-11"])
        return pd.DataFrame({"Close": [100.0, 102.0]}, index=dates)


class _Provider:
    name = "Test provider"

    def ticker(self, _symbol: str):
        return _Ticker()

    def search_news(self, _query: str, _limit: int):
        return []


def test_stock_tool_uses_configurable_provider_boundary() -> None:
    original = get_market_data_provider()
    try:
        set_market_data_provider(_Provider())
        result = get_stock_price("AAPL")
        assert result["price"] == 102.0
        assert result["change_percent"] == 2.0
    finally:
        set_market_data_provider(original)
