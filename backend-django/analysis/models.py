from django.db import models


class BookCharacter(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="characters"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("name", "book")

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
        unique_together = ("name", "book")

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
        unique_together = ("name", "book")

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
        unique_together = ("from_character", "to_character", "book")

    def __str__(self):
        return f"{self.from_character.name} {self.relation_type} {self.to_character.name}"
