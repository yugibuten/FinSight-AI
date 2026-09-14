from tools.stock import get_stock_price


tools = [
    {
        "type": "function",
        "name": "get_stock_price",
        "description": (
            "Get the current stock price, daily price change, "
            "and percentage change for a publicly traded company."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, such as AAPL or MSFT."
                }
            },
            "required": ["ticker"],
            "additionalProperties": False
        }
    }
]


tool_functions = {
    "get_stock_price": get_stock_price
}