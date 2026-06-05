import json
import urllib.error
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from characters.ai import CharacterGenerationError, generate_characters


class FakeBook:
    title = "Dune"

    class _Authors:
        def values_list(self, *a, **k):
            return ["Frank Herbert"]

    authors = _Authors()


def _openrouter_response(payload: dict) -> bytes:
    content = json.dumps(payload)
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")


class _MockResp:
    """Context-manager returned by mocked urlopen."""

    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


@override_settings(OPENROUTER_API_KEY="test-key", OPENROUTER_MODEL="test/model")
class GenerateCharactersTests(SimpleTestCase):
    def test_parses_characters_and_relations(self):
        body = _openrouter_response(
            {
                "characters": [
                    {"name": "Paul Atreides", "role": "Protagonist", "description": "Heir."},
                ],
                "relations": [
                    {"from": "Paul Atreides", "to": "Lady Jessica", "label": "son"},
                ],
            }
        )

        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            data = generate_characters(FakeBook())

        self.assertEqual(data["characters"][0]["name"], "Paul Atreides")
        self.assertEqual(data["relations"][0]["label"], "son")

    def test_invalid_json_raises(self):
        body = json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode("utf-8")

        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            with self.assertRaises(CharacterGenerationError):
                generate_characters(FakeBook())

    @override_settings(OPENROUTER_API_KEY="")
    def test_missing_api_key_raises(self):
        with self.assertRaises(CharacterGenerationError):
            generate_characters(FakeBook())

    def test_missing_relations_key_defaults_to_empty(self):
        body = _openrouter_response(
            {
                "characters": [{"name": "Paul", "role": "Lead", "description": "x"}],
            }
        )

        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            data = generate_characters(FakeBook())

        self.assertEqual(data["relations"], [])

    def test_network_failure_raises(self):
        with patch(
            "characters.ai.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            with self.assertRaises(CharacterGenerationError):
                generate_characters(FakeBook())
