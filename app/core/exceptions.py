class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


class ConfigurationError(AppError):
    def __init__(self, message: str = "FinSight is not fully configured") -> None:
        super().__init__("CONFIGURATION_ERROR", message, 503)


class ProviderRateLimitError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "PROVIDER_RATE_LIMITED",
            "The AI provider is temporarily rate limited. Please try again later.",
            429,
            retryable=True,
        )


class ProviderUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "PROVIDER_UNAVAILABLE",
            "Financial intelligence is temporarily unavailable.",
            502,
            retryable=True,
        )


class QueryTimeoutError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "QUERY_TIMEOUT",
            "The query took too long to complete. Please try again.",
            504,
            retryable=True,
        )


class ResearchNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__("RESEARCH_NOT_FOUND", "The saved research was not found.", 404)
