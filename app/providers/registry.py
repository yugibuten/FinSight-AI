from app.providers.base import MarketDataProvider
from app.providers.yahoo import YahooFinanceProvider


_provider: MarketDataProvider = YahooFinanceProvider()


def get_market_data_provider() -> MarketDataProvider:
    return _provider


def set_market_data_provider(provider: MarketDataProvider) -> None:
    """Override the provider for tests or a future deployment adapter."""
    global _provider
    _provider = provider
