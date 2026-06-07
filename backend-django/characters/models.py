from django.db import models
from django.utils.text import slugify

from .relations import RelationType, relation_group


def unique_character_slug(book, name: str) -> str:
    """Slug unique within one book. Dedups with a numeric suffix."""
    base = slugify(name, allow_unicode=True)[:200] or "character"
    slug = base
    counter = 1
    while Character.objects.filter(book=book, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class CharacterAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    book = models.OneToOneField(
        "books.Book", on_delete=models.CASCADE, related_name="character_analysis"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")
    model = models.CharField(max_length=200, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} [{self.status}]"


class Character(models.Model):
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="characters")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    role = models.CharField(max_length=120, blank=True, default="")
    description = models.TextField(blank=True, default="")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(fields=["book", "slug"], name="unique_book_character_slug"),
        ]

    def __str__(self):
        return f"{self.name} ({self.book.title})"


class CharacterRelation(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="character_relations"
    )
    from_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="relations_from"
    )
    to_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="relations_to"
    )
    relation_type = models.CharField(
        max_length=20, choices=RelationType.choices, default=RelationType.OTHER
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["from_character", "to_character", "relation_type"],
                name="unique_relation_type_per_pair",
            ),
        ]

    @property
    def group(self) -> str:
        return relation_group(self.relation_type)

    def __str__(self):
        return f"{self.from_character.name} → {self.to_character.name} ({self.relation_type})"
