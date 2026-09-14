from typing import Any

import pandas as pd
import yfinance as yf

from app.tools.stock_tool import normalize_symbol, safe_number


def _value(info: dict[str, Any], key: str) -> Any:
    value = info.get(key)
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def get_company_details(ticker: str) -> dict[str, Any]:
    """Return a company profile and key trading metadata."""
    symbol = normalize_symbol(ticker)
    try:
        info = yf.Ticker(symbol).get_info()
        if not info or not (info.get("symbol") or info.get("longName")):
            return {"success": False, "ticker": symbol, "error": "Company not found"}
        return {
            "success": True,
            "ticker": symbol,
            "name": _value(info, "longName") or _value(info, "shortName"),
            "exchange": _value(info, "exchange"),
            "currency": _value(info, "currency"),
            "country": _value(info, "country"),
            "sector": _value(info, "sector"),
            "industry": _value(info, "industry"),
            "website": _value(info, "website"),
            "employees": _value(info, "fullTimeEmployees"),
            "description": _value(info, "longBusinessSummary"),
        }
    except Exception as exc:
        return {"success": False, "ticker": symbol, "error": f"Company data unavailable: {exc}"}


def get_financial_metrics(ticker: str) -> dict[str, Any]:
    """Return valuation, profitability, growth, and balance-sheet metrics."""
    symbol = normalize_symbol(ticker)
    try:
        info = yf.Ticker(symbol).get_info()
        if not info:
            return {"success": False, "ticker": symbol, "error": "Financial data not found"}
        numeric_keys = {
            "market_cap": "marketCap",
            "enterprise_value": "enterpriseValue",
            "trailing_pe": "trailingPE",
            "forward_pe": "forwardPE",
            "price_to_book": "priceToBook",
            "dividend_yield": "dividendYield",
            "profit_margin": "profitMargins",
            "operating_margin": "operatingMargins",
            "return_on_equity": "returnOnEquity",
            "revenue_growth": "revenueGrowth",
            "earnings_growth": "earningsGrowth",
            "total_revenue": "totalRevenue",
            "net_income": "netIncomeToCommon",
            "total_cash": "totalCash",
            "total_debt": "totalDebt",
            "free_cash_flow": "freeCashflow",
            "beta": "beta",
            "fifty_two_week_high": "fiftyTwoWeekHigh",
            "fifty_two_week_low": "fiftyTwoWeekLow",
        }
        metrics = {name: safe_number(info.get(key)) for name, key in numeric_keys.items()}
        if not any(value is not None for value in metrics.values()):
            return {"success": False, "ticker": symbol, "error": "Financial metrics not found"}
        return {
            "success": True,
            "ticker": symbol,
            "currency": info.get("currency"),
            "metrics": metrics,
        }
    except Exception as exc:
        return {"success": False, "ticker": symbol, "error": f"Financial data unavailable: {exc}"}
