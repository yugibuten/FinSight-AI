from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.exceptions import ConfigurationError


class GeminiProvider:
    name = "gemini"

    def generate_synthesis(
        self,
        *,
        model: str,
        contents: str,
        system_instruction: str,
        response_schema: Any,
        tools: list[Any],
        timeout_seconds: float,
    ) -> Any:
        if settings.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is not configured")
        client = genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1_000)),
        )
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    tools=tools or None,
                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(maximum_remote_calls=5)
                        if tools else None
                    ),
                ),
            )
        finally:
            client.close()
