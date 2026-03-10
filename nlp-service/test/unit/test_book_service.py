import pytest
from api.services.book_service import find_sentences_with_both_characters, analyse_text


# --- analyse_text tests ---
def test_analyse_text_counts():
    """Test that function correctly counts characters, words, and tokens."""

    result = analyse_text("Hello world!")
    assert result["char_count"] == 12
    assert result["word_count"] == 2
    assert result["token_count"] == 3


def test_analyse_text_empty_string():
    """Test that function returns zero counts for empty string."""

    result = analyse_text("")
    assert result["char_count"] == 0
    assert result["word_count"] == 0
    assert result["token_count"] == 0


def test_analyse_text_many_spaces():
    """Test that function counts words correctly when multiple spaces are present."""

    result = analyse_text("Hello   world!  This is a test.")
    assert result["char_count"] == 31  # counts all characters including spaces
    assert result["word_count"] == 6  # split() without args ignores multiple spaces
    assert result["token_count"] == 7  # 31 // 4


def test_analyse_text_only_spaces():
    """Test that function counts characters and tokens but zero words when string has only spaces."""

    result = analyse_text("     ")
    assert result["char_count"] == 5
    assert result["word_count"] == 0
    assert result["token_count"] == 1  # 5 // 4


def test_analyse_text_unicode_characters():
    """Test that function counts unicode characters correctly."""

    result = analyse_text("Café Münster")
    assert result["char_count"] == 12  # liczy wszystkie znaki, w tym unicode
    assert result["word_count"] == 2  # split() dzieli na "Café" i "Münster"
    assert result["token_count"] == 3  # 12 // 4


# --- find_sentences_with_both_characters tests ---
def test_unicode_character_name():
    """Test that function correctly matches character names with Unicode characters."""

    content = "Café and Münster walked together."
    result = find_sentences_with_both_characters(content, ["Café", "Münster"])
    assert len(result) == 1
    assert result[0]["pair"] == ["Café", "Münster"]
    assert len(result[0]["sentences"]) == 1


def test_character_namewith_spaces():
    """Test that function correctly matches character names with spaces."""

    content = "Frodo Baggins and Samwise Gamgee walked together."
    result = find_sentences_with_both_characters(
        content, ["Frodo Baggins", "Samwise Gamgee"]
    )
    assert len(result) == 1
    assert result[0]["pair"] == ["Frodo Baggins", "Samwise Gamgee"]
    assert len(result[0]["sentences"]) == 1


def test_special_characters_in_names():
    """Test that function correctly matches character names with special characters."""

    content = "D'Artagnan and Athos fought bravely."
    result = find_sentences_with_both_characters(content, ["D'Artagnan", "Athos"])
    assert len(result) == 1
    assert result[0]["pair"] == ["D'Artagnan", "Athos"]
    assert len(result[0]["sentences"]) == 1


def test_returns_empty_when_no_sentences():
    """Test that function returns empty list when no sentences in content."""

    result = find_sentences_with_both_characters("", ["Frodo", "Sam"])
    assert result == []


def test_returns_empty_when_no_characters():
    """Test that function returns empty list when no characters provided."""

    result = find_sentences_with_both_characters("Frodo and Sam walked.", [])
    assert result == []


def test_returns_empty_when_one_character():
    """Test that function returns empty list when only one character provided."""

    result = find_sentences_with_both_characters("Frodo and Sam walked.", ["Frodo"])
    assert result == []  # combinations(1 element) = brak par


def test_finds_pair_in_same_sentence():
    """Test that function finds sentences containing both characters."""

    result = find_sentences_with_both_characters(
        "Frodo and Sam walked together.", ["Frodo", "Sam"]
    )
    assert len(result) == 1
    assert result[0]["pair"] == ["Frodo", "Sam"]
    assert len(result[0]["sentences"]) == 1


def test_no_match_when_pair_never_in_same_sentence():
    """Test that function returns empty sentences list when characters never appear together."""

    content = "Frodo walked alone. Sam stayed home."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam"])
    assert result == []


def test_include_empty_returns_pair_with_no_sentences():
    """Test that function returns pair with empty sentences list when include_empty is True."""

    content = "Frodo walked alone. Sam stayed home."
    result = find_sentences_with_both_characters(
        content, ["Frodo", "Sam"], include_empty=True
    )
    assert len(result) == 1
    assert result[0]["sentences"] == []


def test_case_insensitive_matching():
    """Test that function matches characters regardless of case."""

    content = "Frodo and sam walked together."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam"])
    assert len(result) == 1
    assert result[0]["pair"] == ["Frodo", "Sam"]
    assert len(result[0]["sentences"]) == 1


def test_three_characters():
    """Test that function finds sentences for multiple character pairs."""

    content = "Frodo, Sam, and Gandalf walked together. Frodo and Gandalf talked."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam", "Gandalf"])

    assert len(result) == 3  # Frodo-Sam, Frodo-Gandalf, Sam-Gandalf
    pairs = {tuple(r["pair"]) for r in result}
    assert ("Frodo", "Sam") in pairs
    assert ("Frodo", "Gandalf") in pairs
    assert ("Sam", "Gandalf") in pairs


def test_sentence_with_three_characters():
    """Test that function includes sentence with all three characters in all pairs."""

    content = "Frodo, Sam, and Gandalf walked together."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam", "Gandalf"])

    for r in result:
        assert len(r["sentences"]) == 1
        assert r["sentences"][0] == content.strip()


# TODO: change regex to implement word boundary and enable this test
@pytest.mark.xfail(
    reason="substring match: 'Ron' found in 'Kronos', word boundary not implemented"
)
def test_substring_name_false_positive():
    """Test that function does not match character names as substrings of other words."""

    content = "Kronos defeated Hermione in battle."
    result = find_sentences_with_both_characters(content, ["Ron", "Hermione"])

    assert result == []  # should be empty, but currently is not
