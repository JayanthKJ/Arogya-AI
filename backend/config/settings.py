"""
config/settings.py
------------------
Centralised configuration using Pydantic BaseSettings.
All values are read from environment variables (or a .env file).
Nothing is hard-coded; secrets never appear in source code.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # ── App metadata ──────────────────────────────────────────────
    APP_NAME: str = "Arogya AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── CORS ──────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins.
    # Example: "http://localhost:3000,https://yourapp.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── LLM provider ─────────────────────────────────────────────
    # Supported values: "openai" | "anthropic" | "mock"
    # Set to "mock" during local development (no API key needed).
    LLM_PROVIDER: str = "mock"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Anthropic / Claude
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "models/gemini-flash-lite-latest"

    # Auth setup stuff
    SECRET_KEY: str  # e.g. openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── LLM generation parameters ─────────────────────────────────
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.4   # lower = safer / more consistent answers

    # ── Rate limiting (requests per minute per IP) ─────────────────
    RATE_LIMIT_PER_MINUTE: int = 20

    # ── Logging ───────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # Reads from a .env file automatically (if present)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # initializing DB link to connect database to the system
    DATABASE_URL: str


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.
    Use `get_settings()` via FastAPI's Depends() to inject config.
    """
    return Settings()
