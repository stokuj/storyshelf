from unittest.mock import patch, MagicMock
import pytest
import api.services.transformers_service as tf_service
from api.services.transformers_service import load_ner_model, DEFAULT_NER_MODEL
from api.models.model import TextContentRequest


# used to ensure that the NER pipelines are cleared before and after each test to prevent state leakage between tests
@pytest.fixture(autouse=True)
def clear_pipelines():
    """Fixture to clear the NER pipelines before and after each test to ensure isolation."""

    tf_service._NER_PIPELINES.clear()
    yield
    tf_service._NER_PIPELINES.clear()


class TestLoadNerModel:
    def test_loads_model_successfully(self):
        fake_pipeline = MagicMock()
        with patch(
            "api.services.transformers_service.pipeline", return_value=fake_pipeline
        ) as mock_pipeline:
            result = load_ner_model(DEFAULT_NER_MODEL)

        assert result is True
        assert tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] is fake_pipeline
        mock_pipeline.assert_called_once_with(
            task="token-classification",
            model=DEFAULT_NER_MODEL,
            aggregation_strategy="first",
            stride=128,
        )

    def test_returns_true_when_already_loaded(self):
        """Test that if the model is already loaded, it returns True without calling the pipeline function."""

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock()

        with patch("api.services.transformers_service.pipeline") as mock_pipeline:
            result = load_ner_model(DEFAULT_NER_MODEL)

        assert result is True
        mock_pipeline.assert_not_called()

    def test_returns_false_when_model_missing(self):
        """Test that if the model cannot be loaded, it returns False and does not add to the pipelines."""

        with patch(
            "api.services.transformers_service.pipeline",
            side_effect=OSError("model not found"),
        ):
            result = load_ner_model("nonexistent/model")

        assert result is False
        assert "nonexistent/model" not in tf_service._NER_PIPELINES


class TestExtractEntities:
    def test_returns_empty_when_model_missing(self):
        """Test that if the model cannot be loaded, extract_entities returns an empty dict."""

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload, model="nonexistent/model")
        assert result == {}

    def test_extracts_entities_successfully(self):
        """Test that extract_entities returns the expected entity groups when the model is loaded."""

        fake_ner_output = [
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "ORG", "word": "OpenAI"},
            {"entity_group": "LOC", "word": "San Francisco"},
            {"entity_group": "MISC", "word": "GPT-3"},
        ]

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(
            return_value=fake_ner_output
        )

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert result["engine"] == "transformers"
        assert result["model_name"] == DEFAULT_NER_MODEL

        assert result["characters"] == {"Alice": 1}
        assert result["organizations"] == {"OpenAI": 1}
        assert result["locations"] == {"San Francisco": 1}
        assert result["miscellaneous"] == {"GPT-3": 1}

        assert isinstance(result["execution_time_seconds"], float)

    def test_counts_duplicate_entities(self):
        """Test that if the NER model returns duplicate entities, extract_entities counts them correctly."""

        fake_ner_output = [
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "ORG", "word": "OpenAI"},
            {"entity_group": "ORG", "word": "OpenAI"},
        ]

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(
            return_value=fake_ner_output
        )

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert result["characters"] == {"Alice": 3}
        assert result["organizations"] == {"OpenAI": 2}
        assert result["locations"] == {}
        assert result["miscellaneous"] == {}

    def test_orders_entities_by_frequency(self):
        """Test that the entities are returned in descending order of frequency."""

        fake_ner_output = [
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": "Bob"},
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": "Charlie"},
            {"entity_group": "PER", "word": "Bob"},
        ]

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(
            return_value=fake_ner_output
        )

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert list(result["characters"].keys()) == ["Alice", "Bob", "Charlie"]

    def test_ignores_empty_word(self):
        """Test that if the NER model returns an entity with an empty word, it is ignored."""

        fake_ner_output = [
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PER", "word": ""},
            {"entity_group": "ORG", "word": "OpenAI"},
            {"entity_group": "LOC", "word": "San Francisco"},
        ]

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(
            return_value=fake_ner_output
        )

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert result["characters"] == {"Alice": 1}
        assert result["organizations"] == {"OpenAI": 1}
        assert result["locations"] == {"San Francisco": 1}
        assert result["miscellaneous"] == {}

    def test_handles_empty_output(self):
        """Test that if the NER model returns an empty list, extract_entities returns empty groups."""

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(return_value=[])

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert result["characters"] == {}
        assert result["organizations"] == {}
        assert result["locations"] == {}
        assert result["miscellaneous"] == {}

    def test_maps_person_aliases(self):
        """Test that if the NER model returns different entity groups for the same word, it is categorized correctly."""

        fake_ner_output = [
            {"entity_group": "PER", "word": "Alice"},
            {"entity_group": "PERSON", "word": "Alice"},
            {"entity_group": "ORG", "word": "OpenAI"},
        ]

        tf_service._NER_PIPELINES[DEFAULT_NER_MODEL] = MagicMock(
            return_value=fake_ner_output
        )

        payload = TextContentRequest(content="Test content")
        result = tf_service.extract_entities(payload)

        assert result["characters"] == {"Alice": 2}
        assert result["organizations"] == {"OpenAI": 1}
        assert result["locations"] == {}
        assert result["miscellaneous"] == {}
