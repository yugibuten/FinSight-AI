from app.planner import build_query_plan


def test_planner_distinguishes_performance_and_valuation_comparisons() -> None:
    performance = build_query_plan("Compare Apple and Microsoft over one year")
    valuation = build_query_plan("Compare Apple and Microsoft valuation and margins")

    assert performance.required_tools == ["compare_stocks"]
    assert performance.period == "1y"
    assert valuation.required_tools == ["compare_financial_metrics"]


def test_planner_resolves_follow_up_entity_from_compact_context() -> None:
    context = [
        {
            "tool_calls": [
                {"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}
            ]
        }
    ]
    plan = build_query_plan("Show its five-year trend", context)
    assert plan.entities == ["AAPL"]
    assert plan.period == "5y"
    assert plan.required_tools == ["get_stock_history"]


def test_planner_resolves_plural_reference_across_recent_turns() -> None:
    context = [
        {"tool_calls": [{"name": "get_stock_price", "arguments": {"ticker": "AAPL"}}]},
        {"tool_calls": [{"name": "get_stock_price", "arguments": {"ticker": "TSLA"}}]},
    ]

    plan = build_query_plan("Compare them", context)

    assert plan.intent == "stock_comparison"
    assert plan.entities == ["AAPL", "TSLA"]
    assert plan.required_tools == ["compare_stocks"]


def test_planner_requires_price_and_news_for_movement_explanation() -> None:
    plan = build_query_plan("Why is Tesla moving today? Use recent news")
    assert plan.required_tools == ["get_stock_price", "get_financial_news"]
    assert plan.requires_live_data is True
