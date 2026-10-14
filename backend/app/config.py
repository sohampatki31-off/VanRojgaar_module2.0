"""Settings from environment variables (prefix VANMITRA_), same convention as the host app."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_JWT_SECRET = "dev-only-change-me"  # noqa: S105 (refused when env=production)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VANMITRA_", env_file=".env", extra="ignore")

    env: str = "development"  # development | test | production
    cors_origins: list[str] = ["*"]

    # Same names and defaults as the host, so a merged host .env works unchanged.
    jwt_secret: str = _DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    mongodb_uri: str = "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true"
    mongodb_db: str = "vanmitra"
    db_connect_timeout_s: int = 3

    # Module 4
    livelihood_demo_endpoints: bool = False  # unauthenticated, serves SAMPLE data: dev only
    livelihood_default_radius_m: int = 5000
    livelihood_max_radius_m: int = 10000
    # "memory": nothing is persisted (dev and tests). "mongo": the real database.
    livelihood_store: Literal["memory", "mongo"] = "memory"
    # Accept the built-in demo users (see app/livelihood/auth.py). NEVER in production.
    livelihood_dev_users: bool = False

    @model_validator(mode="after")
    def _safe_in_production(self) -> "Settings":
        if self.env == "production":
            if self.jwt_secret == _DEV_JWT_SECRET:
                raise ValueError("VANMITRA_JWT_SECRET must be set in production")
            if self.livelihood_dev_users or self.livelihood_demo_endpoints:
                raise ValueError("dev users and demo endpoints must be off in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
