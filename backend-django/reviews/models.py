from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="reviews", db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "user"], name="unique_book_user_review"),
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.handle} → {self.book.title} ({self.rating}/5)"
