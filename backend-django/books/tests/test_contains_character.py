from django.test import TestCase
from rest_framework.test import APIClient

from analysis.models import BookCharacter
from books.models import Book


class ContainsCharacterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book1 = Book.objects.create(title="Harry Potter")
        self.book2 = Book.objects.create(title="Another Book")
        BookCharacter.objects.create(book=self.book1, name="Hermione Granger", mention_count=10)
        BookCharacter.objects.create(book=self.book1, name="Harry Potter", mention_count=20)
        BookCharacter.objects.create(book=self.book2, name="John Smith", mention_count=5)

    def test_finds_book_by_character_name(self):
        response = self.client.get("/api/books/contains-character/?name=Hermione")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertIn(self.book1.pk, ids)
        self.assertNotIn(self.book2.pk, ids)

    def test_case_insensitive(self):
        response = self.client.get("/api/books/contains-character/?name=hermione")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertIn(self.book1.pk, ids)

    def test_substring_match(self):
        response = self.client.get("/api/books/contains-character/?name=Herm")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertIn(self.book1.pk, ids)

    def test_no_duplicates_when_multiple_characters_match(self):
        response = self.client.get("/api/books/contains-character/?name=Harry")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate books in response")

    def test_empty_name_returns_empty(self):
        response = self.client.get("/api/books/contains-character/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["total"], 0)

    def test_paginated_shape(self):
        response = self.client.get("/api/books/contains-character/?name=a")
        self.assertEqual(response.status_code, 200)
        for key in ("data", "page", "per_page", "total"):
            self.assertIn(key, response.data)
