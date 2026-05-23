from django.db import migrations, models
from django.utils.text import slugify


def generate_slugs(apps, schema_editor):
    Book = apps.get_model("books", "Book")
    existing_slugs = set()
    for book in Book.objects.all().order_by("id"):
        base = slugify(book.title)[:200] or "book"
        slug = base
        counter = 1
        while slug in existing_slugs or Book.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        book.slug = slug
        book.save(update_fields=["slug"])
        existing_slugs.add(slug)


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0003_alter_book_page_count_alter_book_year"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="slug",
            field=models.SlugField(blank=True, db_index=False, default="", max_length=255),
        ),
        migrations.RunPython(generate_slugs, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="book",
            name="slug",
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
    ]
