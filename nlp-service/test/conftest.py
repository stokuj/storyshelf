# tests/conftest.py
import os

# Must be set before any import of llm_service (module-level singleton reads the key at import time)
os.environ.setdefault("OPENROUTER_API_KEY", "fake-key")
os.environ.setdefault("NER_MIN_OCCURRENCES", "1")
