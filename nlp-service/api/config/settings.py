"""Centralised application settings loaded from environment variables."""

import os
from importlib.metadata import PackageNotFoundError, version

# --- App ---
try:
    APP_VERSION: str = version("storyweave")
except PackageNotFoundError:
    APP_VERSION = "dev"


# --- CORS ---
CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS: list[str] = os.getenv("CORS_ALLOW_METHODS", "*").split(",")
CORS_ALLOW_HEADERS: list[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")

# --- Celery ---
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

# --- OpenRouter / LLM ---
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
