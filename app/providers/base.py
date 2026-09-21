from typing import Any, Protocol


class MarketDataProvider(Protocol):
    """Boundary between FinSight tools and an external market-data vendor."""

    name: str

    def ticker(self, symbol: str) -> Any: ...

    def search_news(self, query: str, limit: int) -> list[dict[str, Any]]: ...
