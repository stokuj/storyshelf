import pytest
from django.db import IntegrityError


class TestBookCharacter:
    def test_create(self, db, book):
        from analysis.models import BookCharacter

        c = BookCharacter.objects.create(name="Frodo", book=book, mention_count=5)
        assert c.name == "Frodo"
        assert c.mention_count == 5
        assert c.description is None

    def test_name_unique(self, db, book):
        from analysis.models import BookCharacter

        BookCharacter.objects.create(name="Gandalf", book=book)
        with pytest.raises(IntegrityError):
            BookCharacter.objects.create(name="Gandalf", book=book)

    def test_mention_count_default(self, db, book):
        from analysis.models import BookCharacter

        c = BookCharacter.objects.create(name="Sam", book=book)
        assert c.mention_count == 0


class TestCharacterRelationship:
    def test_create(self, db, book, character_a, character_b):
        from analysis.models import CharacterRelationship

        r = CharacterRelationship.objects.create(
            from_character=character_a,
            to_character=character_b,
            relation_type="friend_of",
            book=book,
        )
        assert r.relation_type == "friend_of"

    def test_unique_together(self, db, book, character_a, character_b):
        from analysis.models import CharacterRelationship

        CharacterRelationship.objects.create(
            from_character=character_a,
            to_character=character_b,
            relation_type="friend_of",
            book=book,
        )
        with pytest.raises(IntegrityError):
            CharacterRelationship.objects.create(
                from_character=character_a,
                to_character=character_b,
                relation_type="enemy_of",
                book=book,
            )


class TestBookText:
    def test_text_field_blank_by_default(self, db, book):
        from books.models import Book

        b = Book.objects.get(pk=book.pk)
        assert b.text == ""

    def test_text_field_stores_content(self, db, book):
        from books.models import Book

        book.text = "Frodo and Gandalf met in the Shire."
        book.save()
        b = Book.objects.get(pk=book.pk)
        assert b.text == "Frodo and Gandalf met in the Shire."
