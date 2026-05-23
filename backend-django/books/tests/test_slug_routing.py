from django.http import Http404
from django.test import TestCase

from books.lookups import resolve_book
from books.models import Book


class BookSlugGenerationTest(TestCase):
    def test_slug_generated_on_save(self):
        book = Book.objects.create(title="The Great Gatsby")
        self.assertEqual(book.slug, "the-great-gatsby")

    def test_slug_collision_adds_suffix(self):
        Book.objects.create(title="Dune")
        book2 = Book.objects.create(title="Dune")
        self.assertNotEqual(book2.slug, "dune")
        self.assertTrue(book2.slug.startswith("dune-"))

    def test_slug_not_changed_on_title_update(self):
        book = Book.objects.create(title="Original Title")
        original_slug = book.slug
        book.title = "Changed Title"
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.slug, original_slug)


class ResolveBookTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Hamlet")

    def test_resolve_by_integer_id(self):
        result = resolve_book(str(self.book.pk))
        self.assertEqual(result.pk, self.book.pk)

    def test_resolve_by_slug(self):
        result = resolve_book(self.book.slug)
        self.assertEqual(result.pk, self.book.pk)

    def test_resolve_nonexistent_raises_404(self):
        with self.assertRaises(Http404):
            resolve_book("nonexistent-slug-xyz")
