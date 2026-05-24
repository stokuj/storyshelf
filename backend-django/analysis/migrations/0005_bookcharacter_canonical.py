import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analysis", "0004_bookcharacter_ai_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookcharacter",
            name="canonical",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"canonical__isnull": True},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aliases",
                to="analysis.bookcharacter",
            ),
        ),
        migrations.AddIndex(
            model_name="bookcharacter",
            index=models.Index(fields=["book", "canonical"], name="bookchar_book_canonical_idx"),
        ),
    ]
