from typing import Any

from app.models import FinSightSynthesis, PresentationBlock, PresentationPlan


def _block(
    block_id: str,
    block_type: str,
    data_ref: str,
    span: str = "full",
    variant: str = "default",
    title: str | None = None,
) -> PresentationBlock:
    return PresentationBlock(
        id=block_id,
        type=block_type,
        data_ref=data_ref,
        span=span,
        variant=variant,
        title=title,
    )


def build_presentation(
    synthesis: FinSightSynthesis,
    charts: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
) -> PresentationPlan:
    """Create a safe query-specific UI plan from fields that actually exist."""
    available = {
        "headline": synthesis.headline is not None,
        "metrics": bool(synthesis.metrics),
        "companies": bool(synthesis.companies),
        "insights": bool(synthesis.insights),
        "evidence": bool(synthesis.evidence),
        "news": bool(synthesis.news),
        "sources": bool(sources),
        "tools": bool(tool_calls),
    }
    chart_blocks = [
        _block(
            f"chart-{index}",
            "chart",
            f"charts.{index}",
            "full",
            "comparison" if len(chart.get("series", [])) > 1 else "performance",
        )
        for index, chart in enumerate(charts)
    ]

    response_type = synthesis.response_type
    blocks: list[PresentationBlock] = []

    if response_type == "stock_price":
        layout = "compact"
        if available["headline"]:
            blocks.append(_block("headline", "headline", "headline", variant="price"))
        blocks.append(_block("summary", "summary", "summary", variant="featured"))
        if available["metrics"]:
            blocks.append(_block("metrics", "metric_grid", "metrics", variant="compact"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence"))
    elif response_type == "stock_history":
        layout = "research_dashboard"
        if available["headline"]:
            blocks.append(_block("headline", "headline", "headline", variant="performance"))
        blocks.extend(chart_blocks)
        if available["metrics"]:
            blocks.append(_block("metrics", "metric_grid", "metrics", "one_third"))
        blocks.append(_block("summary", "summary", "summary", "two_thirds", "featured"))
        if available["insights"]:
            blocks.append(_block("insights", "insight_list", "insights", "half"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence", "half"))
    elif response_type == "stock_comparison":
        layout = "comparison_dashboard"
        if available["companies"]:
            blocks.append(_block("companies", "company_grid", "companies", variant="comparison"))
        blocks.extend(chart_blocks)
        if available["metrics"]:
            blocks.append(_block("metrics", "metric_grid", "metrics"))
        blocks.append(_block("summary", "summary", "summary", "two_thirds", "featured"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence", "one_third"))
        if available["insights"]:
            blocks.append(_block("insights", "insight_list", "insights"))
    elif response_type == "financial_news":
        layout = "news_digest"
        if available["headline"]:
            blocks.append(_block("headline", "headline", "headline", variant="compact"))
        blocks.append(_block("summary", "summary", "summary", variant="featured"))
        if available["news"]:
            blocks.append(_block("news", "news_feed", "news"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence"))
    elif response_type == "market_overview":
        layout = "market_dashboard"
        if available["metrics"]:
            blocks.append(_block("metrics", "metric_grid", "metrics", variant="featured"))
        blocks.extend(chart_blocks)
        blocks.append(_block("summary", "summary", "summary", "two_thirds", "featured"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence", "one_third"))
        if available["insights"]:
            blocks.append(_block("insights", "insight_list", "insights"))
    elif response_type == "company_research":
        layout = "research_dashboard"
        if available["companies"]:
            blocks.append(_block("companies", "company_grid", "companies", variant="featured"))
        if available["metrics"]:
            blocks.append(_block("metrics", "metric_grid", "metrics"))
        blocks.append(_block("summary", "summary", "summary", "two_thirds", "featured"))
        if available["insights"]:
            blocks.append(_block("insights", "insight_list", "insights", "one_third"))
        if available["evidence"]:
            blocks.append(_block("evidence", "evidence", "evidence"))
    else:
        layout = "explainer"
        blocks.append(_block("summary", "summary", "summary", variant="featured"))
        if available["insights"]:
            blocks.append(_block("insights", "insight_list", "insights"))

    # Factual responses must expose their evidence trail. Debug activity remains
    # last and collapsed in the frontend.
    if available["sources"]:
        blocks.append(_block("sources", "source_list", "sources"))
    if available["tools"]:
        blocks.append(_block("tools", "tool_activity", "tool_calls", variant="compact"))
    return PresentationPlan(layout=layout, blocks=blocks)
