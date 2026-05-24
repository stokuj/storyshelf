from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class BookCharacterManager(models.Manager):
    """Default manager that excludes hidden characters."""

    def get_queryset(self):
        return super().get_queryset().filter(is_hidden=False)


def _generate_character_slug(name: str, book_id: int) -> str:
    base = slugify(name)[:200] or "character"
    slug = base
    counter = 2
    while BookCharacter.all_objects.filter(slug=slug, book_id=book_id).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class BookCharacter(models.Model):
    objects = BookCharacterManager()
    all_objects = models.Manager()

    class Source(models.TextChoices):
        HUMAN = "human"
        AI = "ai"
        AI_VERIFIED = "ai-verified"

    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="characters"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, default="")
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.AI
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    is_hidden = models.BooleanField(default=False)
    canonical = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aliases",
        limit_choices_to={"canonical__isnull": True},
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "book"], name="unique_character_per_book"),
            models.UniqueConstraint(fields=["slug", "book"], name="unique_character_slug_per_book"),
        ]
        indexes = [
            models.Index(fields=["book", "canonical"], name="bookchar_book_canonical_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_character_slug(self.name, self.book_id)
        super().save(*args, **kwargs)

    @property
    def is_canonical(self):
        return self.canonical_id is None

    def clean(self):
        if self.canonical_id is not None:
            from django.core.exceptions import ValidationError
            if self.canonical_id == self.pk:
                raise ValidationError({"canonical": "A character cannot be its own canonical."})
            if self.canonical.canonical_id is not None:
                raise ValidationError(
                    {"canonical": "Canonical must itself be canonical (no alias chains)."}
                )
            if self.canonical.book_id != self.book_id:
                raise ValidationError({"canonical": "Canonical must belong to the same book."})

    def __str__(self):
        return self.name


class BookPlace(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="places"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "book"], name="unique_place_per_book"),
        ]

    def __str__(self):
        return self.name


class BookOrganization(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="organizations"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "book"], name="unique_org_per_book"),
        ]

    def __str__(self):
        return self.name


class CharacterRelationship(models.Model):
    class RelationType(models.TextChoices):
        PARENT_OF = "parent_of"
        SIBLING_OF = "sibling_of"
        SPOUSE_OF = "spouse_of"
        ANCESTOR_OF = "ancestor_of"
        FRIEND_OF = "friend_of"
        ENEMY_OF = "enemy_of"
        RIVAL_OF = "rival_of"
        MENTOR_OF = "mentor_of"
        LOVER_OF = "lover_of"
        ADMIRES = "admires"
        RULER_OF = "ruler_of"
        COMMANDS = "commands"
        SERVES = "serves"
        MEMBER_OF_FACTION = "member_of_faction"
        FIGHTS_AGAINST = "fights_against"
        PROTECTS = "protects"
        BETRAYS = "betrays"
        SAVES = "saves"
        HUNTS = "hunts"
        KNOWS_SECRET_OF = "knows_secret_of"
        MANIPULATES = "manipulates"
        DECEIVES = "deceives"
        CREATOR_OF = "creator_of"
        CLONE_OF = "clone_of"

    from_character = models.ForeignKey(
        BookCharacter, on_delete=models.CASCADE, related_name="relations_from"
    )
    to_character = models.ForeignKey(
        BookCharacter, on_delete=models.CASCADE, related_name="relations_to"
    )
    relation_type = models.CharField(max_length=30, choices=RelationType.choices)
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="character_relationships"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_character", "to_character", "book"],
                name="unique_character_relation_per_book",
            ),
        ]

    def __str__(self):
        return f"{self.from_character.name} {self.relation_type} {self.to_character.name}"
