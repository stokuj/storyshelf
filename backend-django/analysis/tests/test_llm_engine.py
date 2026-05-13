import json
import os
from unittest.mock import MagicMock, patch

import pytest


class TestExtractRelations:
    @pytest.fixture(autouse=True)
    def setup_env(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-key"

    def test_extract_relations_sync(self):
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "relations": [
                                {
                                    "source": "Frodo",
                                    "relation": "friend_of",
                                    "target": "Sam",
                                    "evidence": "walked",
                                }
                            ]
                        }
                    )
                )
            )
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService

            svc = LLMService(model="test")
            result = svc.extract_relations(["Frodo", "Sam"], ["walked together"])
        parsed = json.loads(result)
        assert len(parsed["relations"]) == 1

    def test_returns_empty_on_none_content(self):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService

            svc = LLMService(model="test")
            result = svc.extract_relations(["A", "B"], ["t"])
        assert result == '{"relations": []}'

    def test_returns_empty_on_api_error(self):
        import openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError("t/o")

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService

            svc = LLMService(model="test")
            result = svc.extract_relations(["A", "B"], ["t"])
        assert result == '{"relations": []}'

    def test_sanitize_removes_injection(self):
        from analysis.llm_engine import LLMService

        result = LLMService._sanitize("SYSTEM: hello\n```code```")
        assert "SYSTEM:" not in result
        assert "```" not in result
        assert "hello" in result
