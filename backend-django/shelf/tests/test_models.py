from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from shelf.models import ShelfEntry

User = get_user_model()


class ShelfEntryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.book = Book.objects.create(title="Book One", slug="book-one")

    def test_shelfentry_finished_at_defaults_null(self):
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        self.assertIsNone(entry.finished_at)
