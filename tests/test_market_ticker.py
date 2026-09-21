import asyncio

from app.api.routes import market


def test_market_ticker_returns_available_quotes_and_uses_cache(monkeypatch) -> None:
    calls: list[str] = []

    def quote(symbol: str) -> dict:
        calls.append(symbol)
        return {
            "success": symbol != "TSLA",
            "ticker": symbol,
            "price": 123.45,
            "currency": "USD",
            "change_percent": 1.25,
            "as_of": "2026-09-16T00:00:00+00:00",
        }

    monkeypatch.setattr(market, "get_stock_price", quote)
    first = asyncio.run(market.market_ticker())
    second = asyncio.run(market.market_ticker())

    assert first == second
    assert first["label"] == "Market snapshot"
    assert first["delayed"] is True
    assert len(first["items"]) == 6
    assert first["items"][0]["symbol"] == "^GSPC"
    assert sorted(calls) == sorted(symbol for _, symbol in market.TICKER_INSTRUMENTS)
