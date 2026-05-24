
class TestFindSentencesWithBothCharacters:
    def test_finds_sentences_with_both(self):
        from analysis.text_parser import find_sentences_with_both_characters

        text = "Frodo walked to Mordor. Sam followed Frodo. Gandalf elsewhere."
        result = find_sentences_with_both_characters(text, ["Frodo", "Sam", "Gandalf"])
        pairs_found = {tuple(r["pair"]) for r in result}
        assert ("Frodo", "Sam") in pairs_found

    def test_case_insensitive(self):
        from analysis.text_parser import find_sentences_with_both_characters

        text = "FRODO and sam walked."
        result = find_sentences_with_both_characters(text, ["Frodo", "Sam"])
        assert len(result) == 1

    def test_word_boundary(self):
        from analysis.text_parser import find_sentences_with_both_characters

        text = "Bilbo and Baggins."
        result = find_sentences_with_both_characters(text, ["Bilbo", "Bag"])
        assert len(result) == 0

    def test_single_character_returns_empty(self):
        from analysis.text_parser import find_sentences_with_both_characters

        result = find_sentences_with_both_characters("Frodo walked.", ["Frodo"])
        assert len(result) == 0
