from typing import Any

import pandas as pd

from app.providers import get_market_data_provider
from app.analytics import calculate_price_analytics

VALID_PERIODS = {"5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}


def normalize_symbol(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if not symbol or len(symbol) > 20:
        raise ValueError("ticker must be a valid exchange symbol")
    return symbol


def safe_number(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def get_stock_price(ticker: str) -> dict[str, Any]:
    """Return the latest close and change from the prior trading session."""
    symbol = normalize_symbol(ticker)
    try:
        stock = get_market_data_provider().ticker(symbol)
        history = stock.history(period="5d", interval="1d", auto_adjust=False)
        closes = history["Close"].dropna() if not history.empty else pd.Series(dtype=float)
        if closes.empty:
            return {"success": False, "ticker": symbol, "error": "No market data found"}

        price = float(closes.iloc[-1])
        previous = float(closes.iloc[-2]) if len(closes) > 1 else None
        change = price - previous if previous is not None else None
        return {
            "success": True,
            "ticker": symbol,
            "as_of": closes.index[-1].isoformat(),
            "price": safe_number(price),
            "currency": stock.fast_info.get("currency") or "Unknown",
            "change": safe_number(change),
            "change_percent": safe_number(change / previous * 100 if previous else None),
        }
    except Exception as exc:
        return {"success": False, "ticker": symbol, "error": f"Market data unavailable: {exc}"}


def get_stock_history(ticker: str, period: str = "6mo") -> dict[str, Any]:
    """Return sampled closes plus overall performance for a supported period."""
    symbol = normalize_symbol(ticker)
    if period not in VALID_PERIODS:
        return {"success": False, "ticker": symbol, "error": f"Unsupported period: {period}"}

    try:
        stock = get_market_data_provider().ticker(symbol)
        history = stock.history(period=period, interval="1d", auto_adjust=False)
        closes = history["Close"].dropna() if not history.empty else pd.Series(dtype=float)
        if closes.empty:
            return {"success": False, "ticker": symbol, "error": "No market data found"}

        stride = max(1, len(closes) // 60)
        sampled = closes.iloc[::stride]
        if sampled.index[-1] != closes.index[-1]:
            sampled = pd.concat([sampled, closes.iloc[[-1]]])
        start, end = float(closes.iloc[0]), float(closes.iloc[-1])
        return {
            "success": True,
            "ticker": symbol,
            "period": period,
            "currency": stock.fast_info.get("currency") or "Unknown",
            "start_price": safe_number(start),
            "end_price": safe_number(end),
            "change_percent": safe_number((end - start) / start * 100 if start else None),
            "high": safe_number(closes.max()),
            "low": safe_number(closes.min()),
            "analytics": calculate_price_analytics(closes),
            "prices": [
                {"date": timestamp.date().isoformat(), "close": safe_number(close)}
                for timestamp, close in sampled.items()
            ],
        }
    except Exception as exc:
        return {"success": False, "ticker": symbol, "error": f"Market data unavailable: {exc}"}


def compare_stocks(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    """Compare deterministic price performance for two to five stocks."""
    if not 2 <= len(tickers) <= 5:
        return {"success": False, "error": "Provide between 2 and 5 tickers"}
    normalized = list(dict.fromkeys(normalize_symbol(ticker) for ticker in tickers))
    if len(normalized) < 2:
        return {"success": False, "error": "Provide at least 2 different tickers"}
    comparisons = []
    series = []
    for ticker in normalized:
        result = get_stock_history(ticker, period)
        prices = result.pop("prices", [])
        if result.get("success") and prices:
            starting_price = prices[0]["close"]
            normalized_prices = [
                {
                    "date": point["date"],
                    "value": safe_number(
                        (point["close"] - starting_price) / starting_price * 100
                    ),
                }
                for point in prices
                if starting_price
            ]
            series.append({"ticker": ticker, "data": normalized_prices})
        comparisons.append(result)
    successful = [item for item in comparisons if item.get("success")]
    ranked = sorted(
        successful,
        key=lambda item: item.get("change_percent") if item.get("change_percent") is not None else float("-inf"),
        reverse=True,
    )
    return {
        "success": bool(successful),
        "period": period,
        "stocks": comparisons,
        "best_performer": ranked[0]["ticker"] if ranked else None,
        "normalized_series": series,
    }
