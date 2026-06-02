from django.test import TestCase

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
