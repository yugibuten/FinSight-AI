from datetime import datetime, timezone
from typing import Any

from app.providers import get_market_data_provider


def _article(raw: dict[str, Any]) -> dict[str, Any]:
    # Newer Yahoo responses put article fields under `content`; older responses
    # return a flat dictionary. Supporting both makes the adapter less brittle.
    content = raw.get("content") if isinstance(raw.get("content"), dict) else raw
    provider = content.get("provider") or {}
    canonical = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
    published = content.get("pubDate") or content.get("providerPublishTime")
    if isinstance(published, (int, float)):
        published = datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
    return {
        "title": content.get("title"),
        "publisher": provider.get("displayName") if isinstance(provider, dict) else provider,
        "published_at": published,
        "summary": content.get("summary") or content.get("description"),
        "url": canonical.get("url") if isinstance(canonical, dict) else canonical,
    }


def get_financial_news(query: str, limit: int = 5) -> dict[str, Any]:
    """Return recent financial news for a company, ticker, or market topic."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("query cannot be empty")
    bounded_limit = max(1, min(limit, 10))
    try:
        results = get_market_data_provider().search_news(clean_query, bounded_limit)
        articles = [_article(item) for item in results[:bounded_limit]]
        articles = [article for article in articles if article["title"]]
        return {
            "success": True,
            "query": clean_query,
            "count": len(articles),
            "articles": articles,
        }
    except Exception as exc:
        return {"success": False, "query": clean_query, "error": f"News unavailable: {exc}"}
