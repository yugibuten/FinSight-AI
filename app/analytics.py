import math
from typing import Any

import pandas as pd


def calculate_price_analytics(closes: pd.Series) -> dict[str, Any]:
    """Calculate reproducible risk and trend metrics from closing prices."""
    clean = closes.dropna().astype(float)
    if clean.empty:
        return {}
    returns = clean.pct_change().dropna()
    running_high = clean.cummax()
    drawdowns = (clean / running_high - 1) * 100
    span_days = (clean.index[-1] - clean.index[0]).days if len(clean) > 1 else 0
    years = span_days / 365.25
    cagr = None
    if years >= 0.08 and clean.iloc[0] > 0 and clean.iloc[-1] > 0:
        cagr = (math.pow(clean.iloc[-1] / clean.iloc[0], 1 / years) - 1) * 100
    volatility = returns.std(ddof=1) * math.sqrt(252) * 100 if len(returns) > 1 else None

    def rounded(value: float | None) -> float | None:
        return round(float(value), 4) if value is not None and not pd.isna(value) else None

    return {
        "cagr_percent": rounded(cagr),
        "annualized_volatility_percent": rounded(volatility),
        "maximum_drawdown_percent": rounded(drawdowns.min()),
        "sma_20": rounded(clean.tail(20).mean()) if len(clean) >= 20 else None,
        "sma_50": rounded(clean.tail(50).mean()) if len(clean) >= 50 else None,
        "observations": len(clean),
    }
