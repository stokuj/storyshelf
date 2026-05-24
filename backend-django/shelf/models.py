from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ"
        READING = "READING"
        READ = "READ"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelf_entries",
        db_index=True,
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="shelf_entries",
        db_index=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WANT_TO_READ
    )
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    # NOTE: validators only run during full_clean(), not on direct .save().
    # Views must call entry.full_clean() before saving when personal_rating is set.
    personal_rating = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_shelf"),
        ]
        ordering = ("-created_at",)

    def clean(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError({"finish_date": "finish_date cannot be before start_date."})


def _unique_shelf_slug_for_user(name: str, user_id: int) -> str:
    """Generate slug unique per user."""
    base = slugify(name)[:70] or "shelf"
    slug = base
    counter = 2
    while Shelf.objects.filter(user_id=user_id, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Shelf(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelves",
        db_index=True,
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, blank=True, default="")
    description = models.TextField(max_length=500, blank=True, default="")
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "slug"], name="unique_user_shelf_slug"),
        ]
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_shelf_slug_for_user(self.name, self.user_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id}:{self.name}"


class ShelfMembership(models.Model):
    shelf = models.ForeignKey(
        Shelf, on_delete=models.CASCADE, related_name="memberships", db_index=True
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="shelf_memberships",
        db_index=True,
    )
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shelf", "book"], name="unique_shelf_book_membership"
            ),
        ]
        ordering = ("position", "-added_at")
        indexes = [
            models.Index(fields=["shelf", "position"], name="shelfmembership_pos_idx"),
        ]

    def __str__(self):
        return f"{self.shelf_id}:{self.book_id}"
