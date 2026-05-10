from django.db import models


class Chapter(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=150, blank=True, default="")
    content = models.TextField()
    analysis_completed = models.BooleanField(default=False)
    char_count = models.IntegerField(null=True, blank=True)
    char_count_clean = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    ner_result = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("chapter_number",)


class StoryCharacter(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    title = models.CharField(max_length=500, blank=True, default="")
    year = models.IntegerField(default=0)
    isbn = models.CharField(max_length=20, blank=True, default="")
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=0)
    position_in_series = models.IntegerField(null=True, blank=True)
    chapters_count = models.IntegerField(default=0)
    ner_completed_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.JSONField(default=list)


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


class BookCharacter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    character = models.ForeignKey(StoryCharacter, on_delete=models.CASCADE)
    mention_count = models.IntegerField(default=0)
    role = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ("book", "character")


class CharacterRelation(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="character_relations"
    )
    source = models.ForeignKey(
        StoryCharacter,
        on_delete=models.CASCADE,
        related_name="relations_as_source",
    )
    target = models.ForeignKey(
        StoryCharacter,
        on_delete=models.CASCADE,
        related_name="relations_as_target",
    )
    relation = models.TextField(null=True, blank=True)
    evidence = models.TextField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("book", "source", "target")
