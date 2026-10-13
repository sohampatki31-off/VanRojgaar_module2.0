"""Settings from environment variables (prefix VANMITRA_), same convention as the host app."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VANMITRA_", env_file=".env", extra="ignore")

    env: str = "development"
    cors_origins: list[str] = ["*"]

    livelihood_demo_endpoints: bool = True
    livelihood_default_radius_m: int = 5000
    livelihood_max_radius_m: int = 10000


@lru_cache
def get_settings() -> Settings:
    return Settings()
