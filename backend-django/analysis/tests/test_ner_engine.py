import pytest
from unittest.mock import patch, MagicMock


class TestLoadNerModel:
    def test_load_with_mock_pipeline(self):
        with patch("analysis.ner_engine.pipeline") as mock_pipeline:
            from analysis.ner_engine import load_ner_model

            result = load_ner_model("test-model")
            assert result is True

    def test_load_returns_false_on_error(self):
        with patch("analysis.ner_engine.pipeline", side_effect=OSError("no model")):
            from analysis.ner_engine import load_ner_model

            result = load_ner_model("missing-model")
            assert result is False


class TestExtractEntities:
    def test_groups_by_entity_type(self):
        fake_pipeline = MagicMock()
        fake_pipeline.return_value = [
            {"word": "Frodo", "entity_group": "PER"},
            {"word": "Frodo", "entity_group": "PER"},
            {"word": "Gandalf", "entity_group": "PER"},
            {"word": "Shire", "entity_group": "LOC"},
            {"word": "Fellowship", "entity_group": "ORG"},
        ]
        with patch("analysis.ner_engine.load_ner_model", return_value=True):
            with patch(
                "analysis.ner_engine._NER_PIPELINES", {"test-model": fake_pipeline}
            ):
                with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                    from analysis.ner_engine import extract_entities

                    result = extract_entities("text", model="test-model")
        assert result["characters"] == {"Frodo": 2, "Gandalf": 1}
        assert result["locations"] == {"Shire": 1}
        assert result["organizations"] == {"Fellowship": 1}
        assert result["miscellaneous"] == {}

    def test_misc_always_empty(self):
        fake_pipeline = MagicMock()
        fake_pipeline.return_value = [
            {"word": "Sword", "entity_group": "MISC"},
        ]
        with patch("analysis.ner_engine.load_ner_model", return_value=True):
            with patch(
                "analysis.ner_engine._NER_PIPELINES", {"test-model": fake_pipeline}
            ):
                from analysis.ner_engine import extract_entities

                result = extract_entities("text", model="test-model")
        assert result["miscellaneous"] == {}

    def test_returns_empty_on_failed_load(self):
        with patch("analysis.ner_engine.load_ner_model", return_value=False):
            from analysis.ner_engine import extract_entities

            result = extract_entities("text")
        assert result == {}
