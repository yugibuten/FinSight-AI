from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FinSight API"
    app_environment: str = "development"
    api_version: str = "v1"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash"
    gemini_fast_model: str = "gemini-3.5-flash"
    gemini_complex_model: str = "gemini-3.5-flash"
    redis_url: SecretStr | None = None
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    query_timeout_seconds: float = Field(default=45, ge=5, le=180)
    provider_timeout_seconds: float = Field(default=20, ge=5, le=120)
    rate_limit_requests: int = Field(default=20, ge=1, le=1_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)
    max_request_bytes: int = Field(default=16_384, ge=1_024, le=1_048_576)
    response_cache_seconds: int = Field(default=30, ge=0, le=300)
    database_url: str = "sqlite:///./data/finsight.db"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
