#test_llm_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from api.services.llm_service import LLMService
from api.services.llm_service import ALL_RELATIONS_STR, RELATION_SCHEMA
import openai

@pytest.mark.asyncio
async def test_returns_json_string():
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
async def test_calls_api_with_correct_model():
    """Testuje czy metoda wywołuje API z poprawnym modelem."""

    fake_response = MagicMock()
    fake_response.choices[0].message.content = '{"relations": []}'

    service = LLMService(model="some-test-model")
    service._client.chat.completions.create = AsyncMock(return_value=fake_response)

    await service.extract_relations(["A", "B"], ["A met B."])

    call_kwargs = service._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "some-test-model"


@pytest.mark.asyncio
async def test_prompt_contains_pair_and_sentences():
    """Testuje czy prompt zawiera nazwy postaci i zdania."""

    fake_response = MagicMock()
    fake_response.choices[0].message.content = '{"relations": []}'

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(return_value=fake_response)

    await service.extract_relations(["Gandalf", "Frodo"], ["Gandalf helped Frodo."])

    call_kwargs = service._client.chat.completions.create.call_args.kwargs
    user_message = call_kwargs["messages"][1]["content"]

    assert "Gandalf" in user_message
    assert "Frodo" in user_message
    assert "Gandalf helped Frodo." in user_message


@pytest.mark.asyncio
async def test_api_timeout():
    """Testuje czy wyjątek timeout propaguje się wyżej."""

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(
        side_effect=openai.APITimeoutError(request=MagicMock())
    )

    with pytest.raises(openai.APITimeoutError):
        await service.extract_relations(["A", "B"], ["A met B."])


@pytest.mark.asyncio
async def test_extract_relations_api_connection_error():
    """Testuje czy błąd połączenia propaguje się wyżej."""

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(
        side_effect=openai.APIConnectionError(request=MagicMock())
    )

    with pytest.raises(openai.APIConnectionError):
        await service.extract_relations(["A", "B"], ["A met B."])


@pytest.mark.asyncio
async def test_extract_relations_returns_none_content():
    """Testuje zachowanie gdy model zwraca None jako content."""

    fake_response = MagicMock()
    fake_response.choices[0].message.content = None

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(return_value=fake_response)

    result = await service.extract_relations(["A", "B"], ["A met B."])
    assert result is None


def test_all_relations_contains_expected_relations():
    """Testuje czy ALL_RELATIONS_STR zawiera wszystkie relacje z RELATION_SCHEMA."""

    for relation in RELATION_SCHEMA.keys():
        assert relation in ALL_RELATIONS_STR


@pytest.mark.asyncio
async def test_api_authentication_error():
    """Testuje czy błąd uwierzytelniania propaguje się wyżej."""

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(
        side_effect=openai.AuthenticationError(message="invalid key", response=MagicMock(), body={})
    )

    with pytest.raises(openai.AuthenticationError):
        await service.extract_relations(["A", "B"], ["A met B."])


@pytest.mark.asyncio
async def test_api_rate_limit_error():
    """Testuje czy błąd limitu zapytań propaguje się wyżej."""

    service = LLMService()
    service._client.chat.completions.create = AsyncMock(
        side_effect=openai.RateLimitError(message="rate limit exceeded", response=MagicMock(), body={})
    )

    with pytest.raises(openai.RateLimitError):
        await service.extract_relations(["A", "B"], ["A met B."])