import pytest
from django.db import IntegrityError


class TestBookCharacter:
    def test_create(self, django_db_setup):
        from analysis.models import BookCharacter

        c = BookCharacter.objects.create(name="Frodo", mention_count=5)
        assert c.name == "Frodo"
        assert c.mention_count == 5
        assert c.description is None

    def test_name_unique(self, django_db_setup):
        from analysis.models import BookCharacter

        BookCharacter.objects.create(name="Gandalf")
        with pytest.raises(IntegrityError):
            BookCharacter.objects.create(name="Gandalf")

    def test_mention_count_default(self, django_db_setup):
        from analysis.models import BookCharacter

        c = BookCharacter.objects.create(name="Sam")
        assert c.mention_count == 0


class TestCharacterRelationship:
    def test_create(self, django_db_setup, book, character_a, character_b):
        from analysis.models import CharacterRelationship

        r = CharacterRelationship.objects.create(
            from_character=character_a,
            to_character=character_b,
            relation_type="friend_of",
            book=book,
        )
        assert r.relation_type == "friend_of"

    def test_unique_together(self, django_db_setup, book, character_a, character_b):
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


class TestChapterNerPending:
    def test_ner_pending_nullable(self, django_db_setup, book):
        from books.models import Chapter

        c = Chapter.objects.create(book=book, chapter_number=1, text="test")
        assert c.ner_pending is None

    def test_ner_pending_stores_json(self, django_db_setup, book):
        from books.models import Chapter

        c = Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="t",
            ner_pending={"characters": {"Frodo": 1}},
        )
        assert c.ner_pending == {"characters": {"Frodo": 1}}
