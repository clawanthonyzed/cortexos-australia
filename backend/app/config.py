"""Application configuration using Pydantic Settings."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "CortexOS Australia"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://cortex:cortex@localhost:5432/cortexos"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    db_echo: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # ── LLM Providers ─────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""

    # Default models
    default_llm_provider: str = "claude"
    default_claude_model: str = "claude-sonnet-4-6"
    default_openai_model: str = "gpt-4o"
    default_gemini_model: str = "gemini-2.5-flash"
    default_openrouter_model: str = "anthropic/claude-sonnet-4-6"

    # ── Observability ─────────────────────────────────────────────────────────
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = True

    # ── Memory ────────────────────────────────────────────────────────────────
    mem0_api_key: str = ""
    mem0_use_local: bool = True  # Use local Qdrant when no API key
    mem0_ollama_url: str = "http://172.17.0.1:11434"  # Docker host Ollama
    mem0_embed_model: str = "nomic-embed-text"

    # ── Knowledge Graph (Neo4j / Graphiti) ────────────────────────────────────
    graphiti_uri: str = "bolt://localhost:7687"
    graphiti_user: str = "neo4j"
    graphiti_password: str = "password"

    # ── Commerce Integrations ─────────────────────────────────────────────────
    etsy_api_key: str = ""
    etsy_shared_secret: str = ""
    gumroad_access_token: str = ""
    lemonsqueezy_api_key: str = ""

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = ""

    # ── Celery ────────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list[str] = ["json"]
    celery_task_time_limit: int = 3600  # 1 hour
    celery_task_soft_time_limit: int = 3300  # 55 min

    @model_validator(mode="after")
    def set_debug_from_env(self) -> "Settings":
        if self.environment == "development":
            self.debug = True
            self.db_echo = False  # Avoid flooding logs even in dev
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
