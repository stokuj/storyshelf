from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book, Chapter
from library.models import Author


class BookListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Test Author")
        cls.book1 = Book.objects.create(
            title="First Book", isbn="111", page_count=200, year=2023
        )
        cls.book1.authors.add(cls.author)
        cls.book1.tags.set([])
        cls.book2 = Book.objects.create(
            title="Second Book", isbn="222", page_count=300, year=2024
        )
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

    def test_post_create_book_as_moderator_returns_201(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post(
            "/api/books/",
            {
                "title": "New Book",
                "author_id": self.author.id,
                "year": 2025,
                "isbn": "333",
                "page_count": 150,
                "genres": ["fantasy"],
                "tags": ["magic"],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(title="New Book")
        self.assertEqual(book.tags.count(), 1)
        self.assertEqual(book.tags.first().name, "magic")

    def test_post_create_book_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/books/",
            {
                "title": "New Book",
                "author_id": self.author.id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_book_unauthenticated_returns_401(self):
        resp = self.client.post(
            "/api/books/",
            {
                "title": "New Book",
                "author_id": self.author.id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_book_missing_author_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/books/", {"title": "No Author"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_book_nonexistent_author_returns_404(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post(
            "/api/books/",
            {
                "title": "Bad Author",
                "author_id": 99999,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class BookDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author")
        cls.book = Book.objects.create(
            title="Detail Book", isbn="444", page_count=250, year=2023
        )
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

    def test_put_update_book_as_moderator_returns_200(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.put(
            f"/api/books/{self.book.id}/",
            {
                "title": "Updated Title",
                "author_id": self.author.id,
                "year": 2025,
                "isbn": "444",
                "page_count": 300,
                "genres": [],
                "tags": [],
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_book_as_moderator_returns_204(self):
        book = Book.objects.create(title="To Delete", isbn="555")
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/books/{book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_delete_book_as_user_returns_403(self):
        book = Book.objects.create(title="To Delete", isbn="666")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/books/{book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_update_book_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            f"/api/books/{self.book.id}/",
            {
                "title": "Hack",
                "author_id": self.author.id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ChapterTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Chapter Book", isbn="777", page_count=100, year=2023
        )

    def test_get_chapters_empty_returns_200_empty(self):
        resp = self.client.get(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    @patch("books.views.analyse_chapter.delay")
    @patch("books.views.ner_chapter.delay")
    def test_post_upload_chapters_as_moderator_returns_201(
        self, mock_ner, mock_analyse
    ):
        self.client.force_authenticate(user=self.moderator)
        content = "Chapter One Content\n\nChapter Two Content"
        file = SimpleUploadedFile("book.txt", content.encode("utf-8"))
        resp = self.client.post(
            f"/api/books/{self.book.id}/chapters/",
            {"file": file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["bookId"], self.book.id)
        self.assertEqual(resp.data["chaptersCreated"], 2)
        self.assertEqual(Chapter.objects.filter(book=self.book).count(), 2)

    def test_post_upload_chapters_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_upload_no_file_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_chapters_as_moderator_returns_204(self):
        Chapter.objects.create(
            book=self.book, chapter_number=1, title="C1", text="text"
        )
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Chapter.objects.filter(book=self.book).count(), 0)


class BookCharactersTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Char Book", isbn="888", page_count=100, year=2023
        )

    def test_get_characters_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/characters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookRelationsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Rel Book", isbn="999", page_count=100, year=2023
        )

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
