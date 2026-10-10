from django.conf import settings
from django.db import models


class Page(models.Model):
    """One OKF document; `content` is the source of truth, other fields are copies for queries."""

    class Type(models.TextChoices):
        BOOK = "book"
        CHARACTER = "character"
        PLACE = "place"
        UNIVERSE = "universe"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pages"
    )
    path = models.TextField()  # '/books/solaris.md', identity within one Wiki
    type = models.CharField(max_length=16, choices=Type.choices)
    title = models.TextField()
    book = models.TextField(null=True, blank=True)
    universe = models.TextField(null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["path"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "path"], name="unique_page_path_per_owner"),
        ]

    def __str__(self):
        return self.path

    @property
    def version(self):
        """Id of the newest PageVersion, the current Version (no separate pointer)."""
        return self.versions.values_list("id", flat=True).first()


class PageVersion(models.Model):
    class Kind(models.TextChoices):
        CREATED = "created"
        GENERATION = "generation"
        PROPOSAL = "proposal"
        EDIT = "edit"

    class Author(models.TextChoices):
        HUMAN = "human"
        AGENT = "agent"

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="versions")
    content = models.TextField()
    kind = models.CharField(max_length=16, choices=Kind.choices)
    author = models.CharField(max_length=8, choices=Author.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
