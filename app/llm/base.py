from typing import Any, Protocol


class LLMProvider(Protocol):
    name: str

    def generate_synthesis(
        self,
        *,
        model: str,
        contents: str,
        system_instruction: str,
        response_schema: Any,
        tools: list[Any],
        timeout_seconds: float,
    ) -> Any: ...
