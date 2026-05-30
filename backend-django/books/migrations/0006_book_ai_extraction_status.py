from django.db import migrations, models


def backfill_extraction_status(apps, schema_editor):
    pass  # analysis app removed; no-op


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0005_bookcharacter_ai_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="ai_extraction_failure_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="book",
            name="ai_extraction_finished_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="book",
            name="ai_extraction_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="book",
            name="ai_extraction_status",
            field=models.CharField(
                choices=[
                    ("none", "None"),
                    ("pending", "Pending"),
                    ("running", "Running"),
                    ("done", "Done"),
                    ("failed", "Failed"),
                ],
                default="none",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_extraction_status, reverse_code=migrations.RunPython.noop),
    ]
