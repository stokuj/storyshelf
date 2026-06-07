from django.db import IntegrityError
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.relations import RelationType


class CharacterRelationModelTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.a = Character.objects.create(book=self.book, name="Paul", slug="paul", order=0)
        self.b = Character.objects.create(book=self.book, name="Jess", slug="jess", order=1)

    def test_group_property(self):
        rel = CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.PARENT,
        )
        self.assertEqual(rel.group, "family")

    def test_unique_per_type_blocks_duplicate(self):
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.SIBLING,
        )
        with self.assertRaises(IntegrityError):
            CharacterRelation.objects.create(
                book=self.book,
                from_character=self.a,
                to_character=self.b,
                relation_type=RelationType.SIBLING,
            )

    def test_same_pair_different_types_allowed(self):
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.SPOUSE,
        )
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.ENEMY,
        )
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 2)
