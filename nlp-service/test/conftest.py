# tests/conftest.py
import pytest

@pytest.fixture(autouse=True)
def set_openrouter_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")