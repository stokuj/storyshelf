from unittest.mock import MagicMock, patch


def make_ent(text, label):
    ent = MagicMock()
    ent.text = text
    ent.label_ = label
    return ent


def make_doc(ents):
    doc = MagicMock()
    doc.ents = ents
    return doc


class TestChunkText:
    def test_single_chunk_for_short_text(self):
        from analysis.ner_engine import chunk_text

        chunks = chunk_text("word " * 100, chunk_size=400, overlap=50)
        assert len(chunks) == 1

    def test_multiple_chunks_for_long_text(self):
        from analysis.ner_engine import chunk_text

        chunks = chunk_text("word " * 1000, chunk_size=400, overlap=50)
        assert len(chunks) > 1

    def test_overlap_means_chunks_share_words(self):
        from analysis.ner_engine import chunk_text

        text = " ".join(str(i) for i in range(500))
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        last_words_of_first = set(chunks[0].split()[-50:])
        first_words_of_second = set(chunks[1].split()[:50])
        assert last_words_of_first & first_words_of_second


class TestExtractEntitiesFromChunks:
    def test_aggregates_characters_across_chunks(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Frodo", "PERSON")]),
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Gandalf", "PERSON")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["characters"]["Frodo"] == 3
        assert result["characters"]["Gandalf"] == 1

    def test_filters_by_min_occurrences(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Rare", "PERSON")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 2):
                result = extract_entities_from_chunks("some text")

        assert "Frodo" not in result["characters"]
        assert "Rare" not in result["characters"]

    def test_returns_empty_when_nlp_fails(self):
        from analysis.ner_engine import extract_entities_from_chunks

        with patch("analysis.ner_engine._get_nlp", return_value=None):
            result = extract_entities_from_chunks("some text")

        assert result == {}

    def test_loc_goes_to_locations(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Shire", "LOC")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["locations"]["Shire"] == 1

    def test_org_goes_to_organizations(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Fellowship", "ORG")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["organizations"]["Fellowship"] == 1
