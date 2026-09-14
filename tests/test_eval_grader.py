from evals.run_evals import grade_case


def test_grader_accepts_expected_tool_and_arguments() -> None:
    case = {
        "expected_tools": ["compare_stocks"],
        "expected_arguments": {
            "compare_stocks": {"tickers": ["AAPL", "MSFT"], "period": "1y"}
        },
    }
    result = {
        "summary": "Apple performed better.",
        "tool_calls": [
            {
                "name": "compare_stocks",
                "arguments": {"tickers": ["MSFT", "AAPL"], "period": "1y"},
            }
        ],
    }
    assert grade_case(case, result, strict=False)["passed"] is True


def test_grader_rejects_wrong_ticker() -> None:
    case = {
        "expected_tools": ["get_stock_price"],
        "expected_arguments": {"get_stock_price": {"ticker": "PAYTM.NS"}},
    }
    result = {
        "summary": "A price",
        "tool_calls": [
            {"name": "get_stock_price", "arguments": {"ticker": "PAYTM"}}
        ],
    }
    assert grade_case(case, result, strict=False)["passed"] is False
