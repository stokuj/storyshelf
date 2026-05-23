from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    title = models.CharField(max_length=500)
    year = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    position_in_series = models.IntegerField(null=True, blank=True)
    text = models.TextField(blank=True, default="")
    avg_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.ManyToManyField("library.Genre", through="BookGenre", related_name="books")

    def __str__(self):
        return self.title


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey("library.Author", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "author"], name="unique_book_author"),
        ]


class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey("library.Tag", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "tag"], name="unique_book_tag"),
        ]


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_genres")
    genre = models.ForeignKey(
        "library.Genre", on_delete=models.CASCADE, related_name="book_genres"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "genre"], name="unique_book_genre"),
        ]
