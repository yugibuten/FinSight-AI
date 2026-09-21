from typing import Any

import yfinance as yf


class YahooFinanceProvider:
    name = "Yahoo Finance"

    def ticker(self, symbol: str) -> Any:
        return yf.Ticker(symbol)

    def search_news(self, query: str, limit: int) -> list[dict[str, Any]]:
        return yf.Search(
            query,
            max_results=0,
            news_count=limit,
            lists_count=0,
            include_research=False,
            timeout=15,
        ).news
