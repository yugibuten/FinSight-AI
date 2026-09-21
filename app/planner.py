import re
from typing import Any

from app.models import QueryPlan


COMPANY_TICKERS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "meta": "META",
    "paytm": "PAYTM.NS",
    "reliance": "RELIANCE.NS",
    "infosys": "INFY.NS",
    "tcs": "TCS.NS",
}
PERIODS = {
    "five days": "5d", "5 days": "5d", "one month": "1mo", "1 month": "1mo",
    "three months": "3mo", "3 months": "3mo", "six months": "6mo", "6 months": "6mo",
    "one year": "1y", "1 year": "1y", "this year": "1y", "two years": "2y",
    "2 years": "2y", "two year": "2y", "five years": "5y", "five year": "5y",
    "5 years": "5y", "5 year": "5y", "six month": "6mo", "three month": "3mo",
    "one year": "1y",
}


def _entities(question: str, context: list[dict[str, Any]]) -> list[str]:
    lowered = question.casefold()
    found = [
        ticker
        for name, ticker in COMPANY_TICKERS.items()
        if re.search(rf"\b{re.escape(name)}\b", lowered)
    ]
    found.extend(re.findall(r"\b[A-Z]{1,5}(?:\.NS)?\b", question))
    reference = re.search(r"\b(it|its|that|they|them|their|those|these|same)\b", lowered)
    if not found and reference:
        plural_reference = reference.group(1) in {"they", "them", "their", "those", "these"}
        turns = context if plural_reference else reversed(context)
        for turn in turns:
            for call in turn.get("tool_calls", []):
                arguments = call.get("arguments", {})
                if arguments.get("ticker"):
                    found.append(str(arguments["ticker"]).upper())
                found.extend(str(item).upper() for item in arguments.get("tickers", []))
            if found and not plural_reference:
                break
    return list(dict.fromkeys(found))[:5]


def build_query_plan(
    question: str,
    context: list[dict[str, Any]] | None = None,
    canvas_action: str | None = None,
    requested_blocks: set[str] | None = None,
) -> QueryPlan:
    lowered = " ".join(question.casefold().split())
    semantic_text = lowered.replace("-", " ")
    context = context or []
    entities = _entities(question, context)
    period = next((value for phrase, value in PERIODS.items() if phrase in semantic_text), None)
    region = "INDIA" if any(word in lowered for word in ("india", "indian", "nifty", "sensex")) else None
    if region is None and any(word in lowered for word in ("global", "world")):
        region = "GLOBAL"
    if region is None and any(word in lowered for word in ("us market", "u.s. market", "s&p", "nasdaq", "dow")):
        region = "US"

    if any(word in lowered for word in ("market overview", "markets performing", "nifty", "sensex")):
        intent, tools = "market_overview", ["get_market_overview"]
    elif any(word in lowered for word in ("why", "moving today", "move today")) and entities:
        intent, tools = "financial_news", ["get_stock_price", "get_financial_news"]
    elif any(word in lowered for word in ("news", "headline", "stories")):
        intent, tools = "financial_news", ["get_financial_news"]
    elif ("compare" in lowered or len(entities) > 1) and any(
        word in lowered for word in ("valuation", "p/e", "profit", "margin", "revenue", "fundamental")
    ):
        intent, tools = "stock_comparison", ["compare_financial_metrics"]
    elif "compare" in lowered or len(entities) > 1:
        intent, tools = "stock_comparison", ["compare_stocks"]
    elif any(word in lowered for word in ("metric", "valuation", "revenue", "margin", "debt", "financials")):
        intent, tools = "company_research", ["get_financial_metrics"]
    elif any(word in lowered for word in ("what does", "industry", "sector", "company details")):
        intent, tools = "company_research", ["get_company_details"]
    elif any(word in lowered for word in ("perform", "history", "trend", "chart", "over the last")):
        intent, tools = "stock_history", ["get_stock_history"]
    elif any(word in lowered for word in ("price", "stock", "quote", "trading")):
        intent, tools = "stock_price", ["get_stock_price"]
    else:
        intent, tools = "general_explanation", []

    return QueryPlan(
        intent=intent,
        entities=entities,
        region=region,
        period=period,
        required_tools=tools,
        requires_live_data=bool(tools),
        canvas_action=canvas_action,
        requested_blocks=sorted(requested_blocks or []),
    )
