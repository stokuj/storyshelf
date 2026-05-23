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

    def test_slug_generated_on_create(self, db, book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=book, name="Hermione Granger", mention_count=5)
        assert char.slug == "hermione-granger"

    def test_slug_collision_within_book_adds_suffix(self, db, book):
        from analysis.models import BookCharacter

        # "Hermione!" and "Hermione?" both slugify to "hermione" — different names, same slug
        BookCharacter.objects.create(book=book, name="Hermione!", mention_count=5)
        char2 = BookCharacter.objects.create(book=book, name="Hermione?", mention_count=3)
        assert char2.slug != "hermione"
        assert char2.slug.startswith("hermione-")

    def test_slug_not_changed_on_update(self, db, book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=book, name="Gandalf", mention_count=10)
        original_slug = char.slug
        char.mention_count = 20
        char.save()
        char.refresh_from_db()
        assert char.slug == original_slug

    def test_default_source_is_ai(self, db, book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=book, name="Frodo", mention_count=8)
        assert char.source == "ai"

    def test_default_is_hidden_false(self, db, book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=book, name="Samwise", mention_count=6)
        assert char.is_hidden is False

    def test_confidence_nullable(self, db, book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=book, name="Aragorn", mention_count=4)
        assert char.confidence is None

    def test_unique_slug_per_book_not_global(self, db, book):
        from analysis.models import BookCharacter
        from books.models import Book

        book2 = Book.objects.create(title="Other Book")
        BookCharacter.objects.create(book=book, name="Legolas", mention_count=3)
        char2 = BookCharacter.objects.create(book=book2, name="Legolas", mention_count=2)
        assert char2.slug == "legolas"


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
