import pytest


class TestAnalyseText:
    def test_basic_counts(self):
        from analysis.text_stats import analyse_text

        result = analyse_text("Hello world")
        assert result["char_count"] == 11
        assert result["char_count_clean"] == 10
        assert result["word_count"] == 2
        assert result["token_count"] > 0

    def test_empty_string(self):
        from analysis.text_stats import analyse_text

        result = analyse_text("")
        assert result["char_count"] == 0
        assert result["word_count"] == 0

    def test_whitespace_only(self):
        from analysis.text_stats import analyse_text

        result = analyse_text("   \n  \t  ")
        assert result["word_count"] == 0
        assert result["char_count_clean"] == 0
