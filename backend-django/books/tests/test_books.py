from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from library.models import Author
from analysis.models import BookCharacter, CharacterRelationship


class BookListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Test Author")
        cls.book1 = Book.objects.create(title="First Book", isbn="111", page_count=200, year=2023)
        cls.book1.authors.add(cls.author)
        cls.book1.tags.set([])
        cls.book2 = Book.objects.create(title="Second Book", isbn="222", page_count=300, year=2024)
        cls.book2.authors.add(cls.author)
        cls.book2.tags.set([])

    def test_get_list_returns_200_with_array(self):
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_get_list_with_search_returns_filtered(self):
        resp = self.client.get("/api/books/?q=First")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [b["title"] for b in resp.data]
        self.assertIn("First Book", titles)

    def test_get_list_with_nonexistent_query_returns_empty(self):
        resp = self.client.get("/api/books/?q=zzzzzzz")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author")
        cls.book = Book.objects.create(title="Detail Book", isbn="444", page_count=250, year=2023)
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_get_detail_returns_200_with_book_and_chapters(self):
        resp = self.client.get(f"/api/books/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("book", resp.data)
        self.assertIn("chapters", resp.data)
        self.assertIn("characters", resp.data)
        self.assertIn("relations", resp.data)
        self.assertIn("reviews", resp.data)
        self.assertEqual(resp.data["book"]["title"], "Detail Book")

    def test_get_nonexistent_book_returns_404(self):
        resp = self.client.get("/api/books/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ChapterListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Chapter Book", isbn="777", page_count=100, year=2023)

    def test_get_chapters_empty_returns_200_empty(self):
        resp = self.client.get(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookCharactersTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Char Book", isbn="888", page_count=100, year=2023)

    def test_get_characters_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/characters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_get_characters_scoped_per_book(self):
        book2 = Book.objects.create(title="Other Book", isbn="888b", page_count=100, year=2023)
        alice = BookCharacter.objects.create(name="Alice", description="", mention_count=5)
        bob = BookCharacter.objects.create(name="Bob", description="", mention_count=3)
        charlie = BookCharacter.objects.create(name="Charlie", description="", mention_count=7)
        dave = BookCharacter.objects.create(name="Dave", description="", mention_count=2)
        CharacterRelationship.objects.create(
            from_character=alice, to_character=bob, relation_type="friend_of", book=self.book
        )
        CharacterRelationship.objects.create(
            from_character=charlie, to_character=dave, relation_type="rival_of", book=book2
        )

        resp_book1 = self.client.get(f"/api/books/{self.book.id}/characters/")
        self.assertEqual(resp_book1.status_code, status.HTTP_200_OK)
        names1 = {c["name"] for c in resp_book1.data}
        self.assertEqual(names1, {"Alice", "Bob"})

        resp_book2 = self.client.get(f"/api/books/{book2.id}/characters/")
        self.assertEqual(resp_book2.status_code, status.HTTP_200_OK)
        names2 = {c["name"] for c in resp_book2.data}
        self.assertEqual(names2, {"Charlie", "Dave"})


class BookRelationsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Rel Book", isbn="999", page_count=100, year=2023)

    def test_get_relations_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/relations/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookSearchByAuthorTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Jane Austen")
        cls.book = Book.objects.create(title="Pride", isbn="000a", year=1813)
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_search_by_author_name_finds_book(self):
        resp = self.client.get("/api/books/?q=austen")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["title"], "Pride")
