"""Centralised application settings loaded from environment variables."""

import os
from importlib.metadata import PackageNotFoundError, version

# --- App ---
try:
    APP_VERSION: str = version("storyweave")
except PackageNotFoundError:
    APP_VERSION = "dev"


# --- CORS ---
_env = os.getenv("APP_ENV", "development").lower()

if _env == "production":
    CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST"]
    CORS_ALLOW_HEADERS: list[str] = ["Content-Type", "Authorization"]
else:
    # development / test — wildcard
    CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = (
        os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    )
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

# --- Celery ---
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

# --- OpenRouter / LLM ---
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL: str = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.5-35b-a3b")
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))

# --- NER ---
NER_MODEL: str = os.getenv(
    "NER_MODEL", "dbmdz/bert-large-cased-finetuned-conll03-english"
)

# --- Kafka ---
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SPRINGSHELF_BASE_URL: str = os.getenv("SPRINGSHELF_BASE_URL", "http://localhost:8080")
