import pytest
from api.services.book_service import analyse_text, find_sentences_with_both_characters


class TestAnalyseText:
    def test_analyse_text_counts_basic(self):
        """Test that function correctly counts characters, words, and tokens."""

        result = analyse_text("Hello world!")
        assert result["char_count"] == 12
        assert result["char_count_clean"] == 10
        assert result["word_count"] == 2
        assert result["token_count"] == 3

    def test_analyse_text_empty_string(self):
        """Test that function returns zero counts for empty string."""

        result = analyse_text("")
        assert result["char_count"] == 0
        assert result["char_count_clean"] == 0
        assert result["word_count"] == 0
        assert result["token_count"] == 0

    def test_analyse_text_multiple_spaces(self):
        """Test that function counts words correctly when multiple spaces are present."""

        result = analyse_text("Hello   world!  This is a test.")
        assert result["char_count"] == 31  # counts all characters including spaces
        assert result["char_count_clean"] == 21
        assert result["word_count"] == 6  # split() without args ignores multiple spaces
        assert result["token_count"] == 10

    def test_analyse_text_only_spaces(self):
        """Test that function counts characters and tokens but zero words when string has only spaces."""

        result = analyse_text("     ")
        assert result["char_count"] == 5
        assert result["char_count_clean"] == 0
        assert result["word_count"] == 0
        assert result["token_count"] == 1

    def test_analyse_text_unicode_chars(self):
        """Test that function counts Unicode characters correctly."""

        result = analyse_text("Café Münster")
        assert result["char_count"] == 12  # liczy wszystkie znaki, w tym unicode
        assert result["char_count_clean"] == 11
        assert result["word_count"] == 2  # split() dzieli na "Café" i "Münster"
        assert result["token_count"] == 6

    def test_analyse_text_newlines_and_tabs(self):
        """Test that function counts characters and tokens correctly when newlines and tabs are present."""

        result = analyse_text("Hello\tworld!\nThis is a test.")
        assert (
            result["char_count"] == 28
        )  # counts all characters including tabs and newlines
        assert result["char_count_clean"] == 21
        assert (
            result["word_count"] == 6
        )  # split() without args ignores tabs and newlines
        assert result["token_count"] == 8

    def test_analyse_text_punctuation(self):
        """Test that function counts characters and tokens correctly when punctuation is present."""

        result = analyse_text("Hello, world! This is a test.")
        assert result["char_count"] == 29  # counts all characters including punctuation
        assert result["char_count_clean"] == 21
        assert result["word_count"] == 6  # split() without args ignores punctuation
        assert result["token_count"] == 9

    def test_analyse_test_numbers(self):
        """Test that function counts characters and tokens correctly when numbers are present."""

        result = analyse_text("The year is 2024.")
        assert (
            result["char_count"] == 17
        )  # counts all characters including spaces and punctuation
        assert result["char_count_clean"] == 13
        assert result["word_count"] == 4  # split() without args splits on spaces
        assert result["token_count"] == 7


class TestFindSentencesWithBothCharacters:
    def test_unicode_names_match(self):
        """Test that function correctly matches character names with Unicode characters."""

        content = "Café and Münster walked together."
        result = find_sentences_with_both_characters(content, ["Café", "Münster"])
        assert len(result) == 1
        assert result[0]["pair"] == ["Café", "Münster"]
        assert len(result[0]["sentences"]) == 1

    def test_names_with_spaces_match(self):
        """Test that function correctly matches character names with spaces."""

        content = "Frodo Baggins and Samwise Gamgee walked together."
        result = find_sentences_with_both_characters(
            content, ["Frodo Baggins", "Samwise Gamgee"]
        )
        assert len(result) == 1
        assert result[0]["pair"] == ["Frodo Baggins", "Samwise Gamgee"]
        assert len(result[0]["sentences"]) == 1

    def test_special_characters_in_names_match(self):
        """Test that function correctly matches character names with special characters."""

        content = "D'Artagnan and Athos fought bravely."
        result = find_sentences_with_both_characters(content, ["D'Artagnan", "Athos"])
        assert len(result) == 1
        assert result[0]["pair"] == ["D'Artagnan", "Athos"]
        assert len(result[0]["sentences"]) == 1

    def test_returns_empty_when_no_sentences(self):
        """Test that function returns empty list when no sentences in content."""

        result = find_sentences_with_both_characters("", ["Frodo", "Sam"])
        assert result == []

    def test_returns_empty_when_no_characters(self):
        """Test that function returns empty list when no characters provided."""

        result = find_sentences_with_both_characters("Frodo and Sam walked.", [])
        assert result == []

    def test_returns_empty_when_one_character(self):
        """Test that function returns empty list when only one character provided."""

        result = find_sentences_with_both_characters("Frodo and Sam walked.", ["Frodo"])
        assert result == []  # combinations(1 element) = brak par

    def test_finds_pair_in_same_sentence(self):
        """Test that function finds sentences containing both characters."""

        result = find_sentences_with_both_characters(
            "Frodo and Sam walked together.", ["Frodo", "Sam"]
        )
        assert len(result) == 1
        assert result[0]["pair"] == ["Frodo", "Sam"]
        assert len(result[0]["sentences"]) == 1

    def test_returns_empty_when_never_together(self):
        """Test that function returns empty sentences list when characters never appear together."""

        content = "Frodo walked alone. Sam stayed home."
        result = find_sentences_with_both_characters(content, ["Frodo", "Sam"])
        assert result == []

    def test_include_empty_returns_pair_with_no_sentences(self):
        """Test that function returns pair with empty sentences list when include_empty is True."""

        content = "Frodo walked alone. Sam stayed home."
        result = find_sentences_with_both_characters(
            content, ["Frodo", "Sam"], include_empty=True
        )
        assert len(result) == 1
        assert result[0]["sentences"] == []

    def test_case_insensitive_matching(self):
        """Test that function matches characters regardless of case."""

        content = "Frodo and sam walked together."
        result = find_sentences_with_both_characters(content, ["Frodo", "Sam"])
        assert len(result) == 1
        assert result[0]["pair"] == ["Frodo", "Sam"]
        assert len(result[0]["sentences"]) == 1

    def test_three_characters_pairs(self):
        """Test that function finds sentences for multiple character pairs."""

        content = "Frodo, Sam, and Gandalf walked together. Frodo and Gandalf talked."
        result = find_sentences_with_both_characters(
            content, ["Frodo", "Sam", "Gandalf"]
        )

        assert len(result) == 3  # Frodo-Sam, Frodo-Gandalf, Sam-Gandalf
        pairs = {tuple(r["pair"]) for r in result}
        assert ("Frodo", "Sam") in pairs
        assert ("Frodo", "Gandalf") in pairs
        assert ("Sam", "Gandalf") in pairs

    def test_sentence_with_three_characters_included(self):
        """Test that function includes sentence with all three characters in all pairs."""

        content = "Frodo, Sam, and Gandalf walked together."
        result = find_sentences_with_both_characters(
            content, ["Frodo", "Sam", "Gandalf"]
        )

        for r in result:
            assert len(r["sentences"]) == 1
            assert r["sentences"][0] == content.strip()

    def test_substring_name_false_positive(self):
        """Test that function does not match character names as substrings of other words."""

        content = "Kronos defeated Hermione in battle."
        result = find_sentences_with_both_characters(content, ["Ron", "Hermione"])

        assert result == []  # should be empty, but currently is not
