from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models, transaction
from django.utils.text import slugify


class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ", "Want to Read"
        READING = "READING", "Reading"
        READ = "READ", "Read"

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
    # Set once when the entry first becomes READ — a stable datetime for feed
    # ordering of "finished" events (finish_date is date-only; auto_now would
    # bump on later current_page edits and resurface old finishes in the feed).
    finished_at = models.DateTimeField(null=True, blank=True)
    current_page = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_shelf"),
        ]
        ordering = ("-created_at",)

    def clean(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError(
                {"finish_date": "finish_date cannot be before start_date."}
            )
        if (
            self.current_page is not None
            and self.book_id is not None
            and self.book.page_count is not None
            and self.current_page > self.book.page_count
        ):
            raise ValidationError(
                {
                    "current_page": (
                        f"current_page ({self.current_page}) cannot exceed "
                        f"book.page_count ({self.book.page_count})."
                    )
                }
            )

    def __str__(self):
        return f"{self.user.handle} · {self.book.title} [{self.status}]"


def _generate_unique_shelf_slug(owner, name: str) -> str:
    base = slugify(name)[:80] or "shelf"  # leave headroom under max_length=100 for "-N" suffix
    slug = base
    counter = 1
    while Shelf.objects.filter(owner=owner, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Shelf(models.Model):
    """A user-curated named collection of books (M5).

    NOTE: distinct from ShelfEntry above. ShelfEntry is reading status
    (Want to Read / Reading / Read), one per user+book. A Shelf is an
    arbitrary collection; ShelfEntry is NOT a member of a Shelf.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelves",
        db_index=True,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)
    slug = models.SlugField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="unique_owner_shelf_slug"),
            models.UniqueConstraint(fields=["owner", "name"], name="unique_owner_shelf_name"),
        ]
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        # Slug is generated once on create and never changes (stable public URLs).
        if not self.slug:
            self.slug = _generate_unique_shelf_slug(self.owner, self.name)
        for _ in range(5):
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return
            except IntegrityError as exc:
                # Only a slug clash is a retryable race; any other integrity error
                # (e.g. a duplicate owner+name) must surface immediately.
                if "slug" not in str(exc).lower():
                    raise
                self.slug = _generate_unique_shelf_slug(self.owner, self.name)
        # Retries exhausted — let the last attempt raise naturally.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.owner.handle} · {self.name}"


class ShelfMembership(models.Model):
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name="memberships")
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="shelf_memberships"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["shelf", "book"], name="unique_shelf_book"),
        ]
        ordering = ("-added_at",)

    def __str__(self):
        return f"{self.shelf.name} · {self.book.title}"
