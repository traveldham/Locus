from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Locus Intelligence API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg:///locus"
    secret_key: str = Field(default="development-only-secret-change-me-123456", min_length=32)
    frontend_url: str = "http://localhost:3000"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    cookie_secure: bool = False

    # Where the sample CSVs live. Blank falls back to the dataset checked out beside the
    # backend; see app/services/providers/sample_data.py.
    sample_data_dir: str | None = None

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
