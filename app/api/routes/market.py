import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.core.cache import cache_key, tool_cache
from app.tools.stock_tool import get_stock_price


router = APIRouter(prefix="/market", tags=["Market"])

TICKER_INSTRUMENTS = (
    ("S&P 500", "^GSPC"),
    ("NASDAQ", "^IXIC"),
    ("NIFTY 50", "^NSEI"),
    ("Apple", "AAPL"),
    ("Microsoft", "MSFT"),
    ("NVIDIA", "NVDA"),
    ("Tesla", "TSLA"),
)
SNAPSHOT_TTL_SECONDS = 60


async def _quote(name: str, symbol: str) -> dict[str, Any]:
    result = await asyncio.to_thread(get_stock_price, symbol)
    return {
        "name": name,
        "symbol": symbol,
        "price": result.get("price"),
        "currency": result.get("currency"),
        "change_percent": result.get("change_percent"),
        "as_of": result.get("as_of"),
        "available": bool(result.get("success")),
    }


@router.get("/ticker", summary="Get a cached market ticker snapshot")
async def market_ticker() -> dict[str, Any]:
    key = cache_key("market_ticker", {"symbols": [item[1] for item in TICKER_INSTRUMENTS]})
    cache_hit, cached = tool_cache.get(key)
    if cache_hit:
        return cached

    quotes = await asyncio.gather(*(_quote(name, symbol) for name, symbol in TICKER_INSTRUMENTS))
    response = {
        "label": "Market snapshot",
        "delayed": True,
        "items": [quote for quote in quotes if quote["available"]],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    tool_cache.set(key, response, SNAPSHOT_TTL_SECONDS)
    return response
