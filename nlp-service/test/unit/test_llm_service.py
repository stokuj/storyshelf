# tests/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
os.environ["OPENROUTER_API_KEY"] = "fake-key"
from api.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_extract_relations_returns_json_string():
    """Testuje czy metoda przy fałszywej odpowiedzi z API zwraca poprawny format JSON."""

    # Przygotuj fałszywą odpowiedź z "API"
    fake_response = MagicMock()
    fake_response.choices[0].message.content = '{"relations": []}'

    service = LLMService()

    # Podmień prawdziwy klient na mocka
    service._client.chat.completions.create = AsyncMock(return_value=fake_response)

    result = await service.extract_relations(
        pair=["Gandalf", "Frodo"],
        sentences=["Gandalf helped Frodo carry the burden."]
    )

    assert isinstance(result, str)
    assert "relations" in result

@pytest.mark.asyncio
async def test_extract_relations_calls_api_with_correct_model():
    """Testuje czy metoda wywołuje API z poprawnym modelem."""

    fake_response = MagicMock()
    fake_response.choices[0].message.content = '{"relations": []}'

    service = LLMService(model="some-test-model")
    service._client.chat.completions.create = AsyncMock(return_value=fake_response)

    await service.extract_relations(["A", "B"], ["A met B."])

    call_kwargs = service._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "some-test-model"