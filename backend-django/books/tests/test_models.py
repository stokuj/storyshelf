from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase

from books.models import Book


class BookIsbnUniqueTest(APITestCase):
    def test_duplicate_isbn_raises_integrity_error(self):
        Book.objects.create(title="Book A", isbn="978-0-123", year=2020, page_count=100)
        with self.assertRaises(IntegrityError):
            Book.objects.create(title="Book B", isbn="978-0-123", year=2021, page_count=200)

    def test_two_books_without_isbn_allowed(self):
        Book.objects.create(title="Book A", isbn=None, year=2020, page_count=100)
        Book.objects.create(title="Book B", isbn=None, year=2021, page_count=200)
        self.assertEqual(Book.objects.filter(isbn__isnull=True).count(), 2)


class BookValidatorsTest(APITestCase):
    def test_year_below_1_raises_validation_error(self):
        book = Book(title="Bad Year", isbn="111", year=0, page_count=100)
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_page_count_below_1_raises_validation_error(self):
        book = Book(title="No Pages", isbn="222", year=2020, page_count=0)
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_valid_book_passes_full_clean(self):
        book = Book(title="Good Book", isbn="333", year=2020, page_count=300)
        book.full_clean()  # nie powinno rzucić
