
from api.services.book_service import find_sentences_with_both_characters


def test_returns_empty_when_no_characters():
    result = find_sentences_with_both_characters("Frodo and Sam walked.", [])
    assert result == []


def test_returns_empty_when_one_character():
    result = find_sentences_with_both_characters("Frodo and Sam walked.", ["Frodo"])
    assert result == []  # combinations(1 element) = brak par


def test_finds_pair_in_same_sentence():
    result = find_sentences_with_both_characters("Frodo and Sam walked together.", ["Frodo", "Sam"])
    assert len(result) == 1
    assert result[0]["pair"] == ["Frodo", "Sam"]
    assert len(result[0]["sentences"]) == 1


def test_no_match_when_pair_never_in_same_sentence():
    content = "Frodo walked alone. Sam stayed home."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam"])
    assert result == []


def test_include_empty_returns_pair_with_no_sentences():
    content = "Frodo walked alone. Sam stayed home."
    result = find_sentences_with_both_characters(content, ["Frodo", "Sam"], include_empty=True)
    assert len(result) == 1
    assert result[0]["sentences"] == []