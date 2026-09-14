stocks = {
    "AAPL": {
        "price": 231.45,
        "currency": "USD",
        "change": 2.31,
        "change_percent": 1.01
    },
    "MSFT": {
        "price": 521.30,
        "currency": "USD",
        "change": -1.24,
        "change_percent": -0.24
    },
    "TSLA": {
        "price": 339.03,
        "currency": "USD",
        "change": 4.52,
        "change_percent": 1.35
    }
}


def get_stock_price(ticker: str):
    ticker = ticker.upper()

    if ticker not in stocks:
        return {
            "success": False,
            "error": f"Stock {ticker} not found"
        }

    return {
        "success": True,
        "ticker": ticker,
        **stocks[ticker]
    }


print(get_stock_price("AAPL"))