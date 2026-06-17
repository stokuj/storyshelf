from django.core.management.base import BaseCommand, CommandError

from books.models import Book
from characters.models import (
    Character,
    CharacterAnalysis,
    CharacterRelation,
    unique_character_slug,
)
from characters.relations import RelationType


class Command(BaseCommand):
    help = "Seed a deterministic DONE character analysis for E2E/dev (no LLM call)."

    def add_arguments(self, parser):
        parser.add_argument("slug", help="Book slug to attach characters to.")

    def handle(self, *args, **options):
        try:
            book = Book.objects.get(slug=options["slug"])
        except Book.DoesNotExist as exc:
            raise CommandError(f"No book with slug {options['slug']!r}") from exc

        CharacterRelation.objects.filter(book=book).delete()
        Character.objects.filter(book=book).delete()
        CharacterAnalysis.objects.update_or_create(
            book=book,
            defaults={"status": CharacterAnalysis.Status.DONE, "error_message": ""},
        )
        frodo = Character.objects.create(
            book=book,
            name="Frodo",
            slug=unique_character_slug(book, "Frodo"),
            role="Ring-bearer",
            description="A hobbit of the Shire who carries the One Ring.",
            order=0,
        )
        sam = Character.objects.create(
            book=book,
            name="Sam",
            slug=unique_character_slug(book, "Sam"),
            role="Companion",
            description="Frodo's loyal friend and gardener.",
            order=1,
        )
        CharacterRelation.objects.create(
            book=book,
            from_character=frodo,
            to_character=sam,
            relation_type=RelationType.FRIEND,
        )
        self.stdout.write(self.style.SUCCESS(f"Seeded characters for {book.slug}"))
