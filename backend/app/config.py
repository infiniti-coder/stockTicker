from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = "http://localhost:8000/auth/callback"
    session_secret: str = "dev-only-insecure-secret"
    database_url: str = "sqlite:///./data/app.db"
    frontend_url: str = "http://localhost:5173"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_enabled: bool = True
    anthropic_api_key: str = ""

    @property
    def use_mock_upstox(self) -> bool:
        """Always true: app/upstox_client/__init__.py always returns the
        mock client now (see get_upstox_client). Kept as a property, not a
        credential check, so it stays truthful regardless of whether
        UPSTOX_API_KEY/SECRET happen to be set in .env."""
        return True


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.database_url.startswith("sqlite:///./"):
        db_path = Path(settings.database_url.removeprefix("sqlite:///./"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
