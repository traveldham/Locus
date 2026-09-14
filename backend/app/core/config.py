from functools import lru_cache
from typing import Literal

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

    # Celery moves audit generation off the request. `always_eager` runs tasks inline
    # in the calling process, which is what the test suite and the CLI export use.
    redis_url: str = "redis://localhost:6379/0"
    celery_always_eager: bool = False
    audit_job_timeout_seconds: int = Field(default=900, ge=30, le=7200)
    # A chat turn is someone waiting at a keyboard, so it is bounded far tighter than an
    # audit. The task sets this per-task: the Celery-wide limit is the audit's.
    agent_turn_timeout_seconds: int = Field(default=180, ge=30, le=600)

    # A snapshot read runs in its own repeatable-read session, so a request that takes
    # one holds two connections at once. Size the pool for that, not for one each.
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)

    # A language model drafts suggestions for fields the profile audit finds missing or
    # weak. Which one is `llm_provider`: "vertex" uses Vertex AI with the machine's
    # Google application default credentials, "gemini" uses the Gemini Developer API
    # with an API key. Nothing configured means the audit runs without suggestions; it
    # never fails because of them.
    suggestions_enabled: bool = True
    suggestions_timeout_seconds: int = Field(default=60, ge=5, le=300)
    llm_provider: Literal["vertex", "gemini"] = "vertex"
    vertex_project: str | None = None
    vertex_location: str = "global"
    vertex_model: str = "gemini-3.8-flash"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

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
