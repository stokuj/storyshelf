from django.core.validators import MinValueValidator
from django.db import models


class Chapter(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=150, blank=True, default="")
    text = models.TextField()
    analysis_completed = models.BooleanField(default=False)
    char_count = models.IntegerField(null=True, blank=True)
    char_count_clean = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    ner_pending = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("chapter_number",)


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    title = models.CharField(max_length=500)
    year = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    position_in_series = models.IntegerField(null=True, blank=True)
    chapters_count = models.IntegerField(default=0)
    ner_completed_count = models.IntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.ManyToManyField("library.Genre", through="BookGenre", related_name="books")


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey("library.Author", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        unique_together = ("book", "author")


class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey("library.Tag", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("book", "tag")


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_genres")
    genre = models.ForeignKey("library.Genre", on_delete=models.CASCADE, related_name="book_genres")

    class Meta:
        unique_together = ["book", "genre"]
