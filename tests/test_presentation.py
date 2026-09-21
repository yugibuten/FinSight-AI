import pytest

from app.models import FinSightSynthesis
from app.presentation import build_presentation


@pytest.mark.parametrize(
    ("response_type", "expected_layout"),
    [
        ("stock_price", "compact"),
        ("stock_history", "research_dashboard"),
        ("stock_comparison", "comparison_dashboard"),
        ("company_research", "research_dashboard"),
        ("financial_news", "news_digest"),
        ("market_overview", "market_dashboard"),
        ("general_explanation", "explainer"),
    ],
)
def test_query_type_selects_its_own_layout(
    response_type: str, expected_layout: str
) -> None:
    synthesis = FinSightSynthesis.model_validate(
        {
            "response_type": response_type,
            "title": "Test",
            "summary": "A grounded summary.",
            "headline": {"label": "Price", "value": "$100", "change": "+1%"},
            "insights": ["Momentum is positive."],
            "metrics": [{"name": "Return", "value": "1%"}],
            "companies": [{"ticker": "TEST", "name": "Test Inc."}],
            "news": [{"title": "Test story"}],
            "evidence": [{"claim": "It rose", "metric": "Return", "value": "1%"}],
        }
    )
    plan = build_presentation(
        synthesis,
        charts=[{"id": "chart", "series": [{"name": "TEST", "data": []}]}],
        sources=[{"title": "Source"}],
        tool_calls=[{"name": "get_stock_price"}],
    )

    assert plan.layout == expected_layout
    assert plan.blocks[0].type == "direct_answer"
    assert next(block for block in reversed(plan.blocks) if block.type != "source_list").type == "summary"
    assert plan.blocks[-1].type == "source_list"
    assert all(block.type != "tool_activity" for block in plan.blocks)


def test_plan_never_references_empty_optional_data() -> None:
    synthesis = FinSightSynthesis(
        response_type="market_overview",
        title="Markets",
        summary="No market data was available.",
    )
    plan = build_presentation(synthesis, charts=[], sources=[], tool_calls=[])

    assert [(block.type, block.data_ref) for block in plan.blocks] == [
        ("direct_answer", "direct_answer"),
        ("summary", "summary")
    ]


def test_chart_references_are_indexed_and_allow_listed() -> None:
    synthesis = FinSightSynthesis(
        response_type="stock_history",
        title="History",
        summary="Performance summary.",
    )
    plan = build_presentation(
        synthesis,
        charts=[
            {"id": "one", "series": [{"name": "A", "data": []}]},
            {"id": "two", "series": [{"name": "A"}, {"name": "B"}]},
        ],
        sources=[],
        tool_calls=[],
    )
    chart_blocks = [block for block in plan.blocks if block.type == "chart"]

    assert [block.data_ref for block in chart_blocks] == ["charts.0", "charts.1"]
    assert [block.variant for block in chart_blocks] == ["performance", "comparison"]
