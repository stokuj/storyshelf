from collections import defaultdict

import django.core.validators
from django.db import migrations, models
from django.utils.text import slugify


def backfill_character_slugs(apps, schema_editor):
    BookCharacter = apps.get_model("analysis", "BookCharacter")
    by_book = defaultdict(list)
    for char in BookCharacter.objects.all().order_by("id"):
        by_book[char.book_id].append(char)

    for book_id, chars in by_book.items():
        used_slugs = set()
        for char in chars:
            base = slugify(char.name)[:200] or "character"
            slug = base
            counter = 2
            while slug in used_slugs:
                slug = f"{base}-{counter}"
                counter += 1
            used_slugs.add(slug)
            char.slug = slug
            char.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("analysis", "0003_alter_bookcharacter_unique_together_and_more"),
        ("books", "0005_bookcharacter_ai_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookcharacter",
            name="confidence",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0.0),
                    django.core.validators.MaxValueValidator(1.0),
                ],
            ),
        ),
        migrations.AddField(
            model_name="bookcharacter",
            name="is_hidden",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="bookcharacter",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="bookcharacter",
            name="source",
            field=models.CharField(
                choices=[("human", "Human"), ("ai", "Ai"), ("ai-verified", "Ai Verified")],
                default="ai",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_character_slugs, reverse_code=migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="bookcharacter",
            constraint=models.UniqueConstraint(
                fields=("slug", "book"), name="unique_character_slug_per_book"
            ),
        ),
    ]
