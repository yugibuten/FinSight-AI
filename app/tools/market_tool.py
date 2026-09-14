from typing import Any

from app.tools.stock_tool import get_stock_price


MARKET_INDICES = {
    "US": {"S&P 500": "^GSPC", "Nasdaq Composite": "^IXIC", "Dow Jones": "^DJI"},
    "INDIA": {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "NIFTY Bank": "^NSEBANK"},
    "GLOBAL": {"S&P 500": "^GSPC", "NIFTY 50": "^NSEI", "FTSE 100": "^FTSE", "Nikkei 225": "^N225"},
}


def get_market_overview(region: str = "US") -> dict[str, Any]:
    """Return latest levels and daily moves for major market indices."""
    normalized = region.strip().upper()
    if normalized not in MARKET_INDICES:
        return {
            "success": False,
            "region": normalized,
            "error": "Unsupported region. Choose US, INDIA, or GLOBAL",
        }
    indices = []
    for name, ticker in MARKET_INDICES[normalized].items():
        result = get_stock_price(ticker)
        indices.append({"name": name, **result})
    return {
        "success": any(index.get("success") for index in indices),
        "region": normalized,
        "indices": indices,
    }
