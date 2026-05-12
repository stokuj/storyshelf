from django.db import migrations


def upgrade_moderator_to_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="MODERATOR").update(role="ADMIN")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_remove_moderator_role"),
    ]

    operations = [
        migrations.RunPython(
            upgrade_moderator_to_admin,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
