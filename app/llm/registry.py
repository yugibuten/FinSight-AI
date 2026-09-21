from app.llm.base import LLMProvider
from app.llm.gemini import GeminiProvider


_provider: LLMProvider = GeminiProvider()


def get_llm_provider() -> LLMProvider:
    return _provider


def set_llm_provider(provider: LLMProvider) -> None:
    global _provider
    _provider = provider
