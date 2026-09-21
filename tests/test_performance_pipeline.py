from threading import Event
from types import SimpleNamespace

from app.models import FinSightSynthesis
from app.orchestrator import answer_question
import app.orchestrator as orchestrator


def test_direct_price_uses_no_llm_fast_path(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "_get_stock_price",
        lambda ticker: {
            "success": True,
            "ticker": ticker,
            "price": 200,
            "currency": "USD",
            "change_percent": 1.5,
            "as_of": "2026-09-14",
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "get_llm_provider",
        lambda: (_ for _ in ()).throw(AssertionError("LLM should not be called")),
    )

    result = answer_question("What is Apple's stock price?")
    assert result["headline"]["value"] == "200.00 USD"
    assert result["performance"]["fast_path"] is True
    assert result["performance"]["provider_ms"] == 0


def test_independent_planned_tools_execute_concurrently(monkeypatch) -> None:
    price_started = Event()
    news_started = Event()

    def price(ticker: str) -> dict:
        price_started.set()
        assert news_started.wait(0.5)
        return {"success": True, "ticker": ticker, "price": 200, "currency": "USD", "change_percent": 1}

    def news(query: str, limit: int) -> dict:
        news_started.set()
        assert price_started.wait(0.5)
        return {"success": True, "query": query, "articles": []}

    class Provider:
        name = "test"

        def generate_synthesis(self, **kwargs):
            assert kwargs["tools"] == []
            return SimpleNamespace(
                parsed=FinSightSynthesis(
                    response_type="financial_news",
                    title="Tesla movement",
                    summary="Tesla moved with no matching recent articles.",
                ),
                text=None,
            )

    monkeypatch.setattr(orchestrator, "_get_stock_price", price)
    monkeypatch.setattr(orchestrator, "_get_financial_news", news)
    monkeypatch.setattr(orchestrator, "get_llm_provider", lambda: Provider())
    monkeypatch.setattr(orchestrator.settings, "gemini_api_key", SimpleNamespace(get_secret_value=lambda: "test"))

    result = answer_question("Why is Tesla moving today? Use recent news")
    assert sorted(call["name"] for call in result["tool_calls"]) == [
        "get_financial_news",
        "get_stock_price",
    ]
    assert result["performance"]["fast_path"] is False
    assert result["performance"]["model"] == orchestrator.settings.gemini_complex_model
