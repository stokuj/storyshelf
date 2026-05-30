from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


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
