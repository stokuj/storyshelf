from django.db import IntegrityError
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation, unique_character_slug
from characters.relations import RelationType


class UniqueCharacterSlugTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")

    def test_unicode_name_keeps_unicode_slug(self):
        self.assertEqual(unique_character_slug(self.book, "Цири"), "цири")

    def test_pure_symbol_name_falls_back_to_character(self):
        self.assertEqual(unique_character_slug(self.book, "★"), "character")


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
