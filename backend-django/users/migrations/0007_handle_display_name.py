from django.db import migrations, models


def backfill_display_name(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(display_name="").update(display_name=models.F("handle"))


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_remove_user_role"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="username",
            new_name="handle",
        ),
        migrations.AddField(
            model_name="user",
            name="display_name",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.RunPython(backfill_display_name, migrations.RunPython.noop),
    ]
