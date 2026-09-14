from unittest.mock import patch

from app.tools.company_tool import get_company_details, get_financial_metrics
from app.tools.market_tool import get_market_overview
from app.tools.news_tool import get_financial_news


def test_company_and_metric_adapters() -> None:
    info = {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "sector": "Technology",
        "marketCap": 1000,
        "trailingPE": 20.5,
    }
    with patch("app.tools.company_tool.yf.Ticker") as ticker:
        ticker.return_value.get_info.return_value = info
        assert get_company_details("AAPL")["name"] == "Apple Inc."
        assert get_financial_metrics("AAPL")["metrics"]["market_cap"] == 1000.0


def test_news_adapter_keeps_source_url() -> None:
    raw_news = [
        {
            "content": {
                "title": "Markets rise",
                "provider": {"displayName": "Example News"},
                "pubDate": "2026-08-19T00:00:00Z",
                "summary": "A market summary",
                "canonicalUrl": {"url": "https://example.com/article"},
            }
        }
    ]
    with patch("app.tools.news_tool.yf.Search") as search:
        search.return_value.news = raw_news
        result = get_financial_news("markets", 5)
    assert result["articles"][0]["publisher"] == "Example News"
    assert result["articles"][0]["url"] == "https://example.com/article"


def test_market_overview_region_validation() -> None:
    result = get_market_overview("MARS")
    assert result["success"] is False
    assert "US, INDIA, or GLOBAL" in result["error"]
