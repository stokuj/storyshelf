from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from analysis.models import BookCharacter
from books.models import Book
from books.serializers import BookDetailSerializer, BookListSerializer
from library.models import Author, Genre, Tag

User = get_user_model()


class BookListSerializerTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Test Book", isbn="tb001", year=2023)

    def test_author_none_when_no_authors(self):
        data = BookListSerializer(self.book).data
        self.assertIsNone(data["author"])

    def test_author_single_author(self):
        author = Author.objects.create(name="Single Author")
        self.book.authors.add(author)
        data = BookListSerializer(self.book).data
        self.assertEqual(data["author"], "Single Author")

    def test_author_multiple_returns_first_only(self):
        a1 = Author.objects.create(name="First Author")
        a2 = Author.objects.create(name="Second Author")
        self.book.authors.add(a1, a2)
        data = BookListSerializer(self.book).data
        self.assertEqual(data["author"], "First Author")

    def test_genres_empty_list(self):
        data = BookListSerializer(self.book).data
        self.assertEqual(data["genres"], [])

    def test_genres_multiple(self):
        g1 = Genre.objects.create(name="Fantasy")
        g2 = Genre.objects.create(name="Sci-Fi")
        self.book.genres.add(g1, g2)
        data = BookListSerializer(self.book).data
        self.assertEqual(sorted(data["genres"]), ["Fantasy", "Sci-Fi"])

    def test_tags_empty_list(self):
        data = BookListSerializer(self.book).data
        self.assertEqual(data["tags"], [])

    def test_tags_multiple(self):
        t1 = Tag.objects.create(name="classic")
        t2 = Tag.objects.create(name="bestseller")
        self.book.tags.add(t1, t2)
        data = BookListSerializer(self.book).data
        self.assertEqual(sorted(data["tags"]), ["bestseller", "classic"])


class BookDetailSerializerTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Detail Book", isbn="db001", year=2023)

    def test_shelf_entry_null_for_anonymous(self):
        data = BookDetailSerializer(self.book, context={"request": None}).data
        self.assertIsNone(data["shelfEntry"])

    def test_analysis_status_false_when_no_characters(self):
        data = BookDetailSerializer(self.book, context={"request": None}).data
        self.assertFalse(data["book"]["analysisStatus"]["analysisFinished"])


class BookDetailCharacterFilterTest(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Test", description="")
        self.canonical = BookCharacter.all_objects.create(
            book=self.book, name="Harry", mention_count=10,
            is_hidden=False,
        )
        self.alias = BookCharacter.all_objects.create(
            book=self.book, name="Mr. Potter", mention_count=3,
            is_hidden=False, canonical=self.canonical,
        )
        self.hidden = BookCharacter.all_objects.create(
            book=self.book, name="Ghost", mention_count=1,
            is_hidden=True,
        )
        self.url = f"/api/books/{self.book.pk}/"

    def test_anon_sees_only_canonical_visible_characters(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [c["name"] for c in resp.data["characters"]]
        self.assertIn("Harry", names)
        self.assertNotIn("Mr. Potter", names)
        self.assertNotIn("Ghost", names)

    def test_admin_sees_all_characters(self):
        admin = User.objects.create_user(
            email="admin@test.com", handle="admin", password="pw123456", is_staff=True
        )
        self.client.force_authenticate(user=admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [c["name"] for c in resp.data["characters"]]
        self.assertIn("Mr. Potter", names)
        self.assertIn("Ghost", names)
