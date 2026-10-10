from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from users.models import User
from wiki import okf, services

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class Command(BaseCommand):
    help = "Load the Wiedźmin + Solaris demo Pages into a user's Wiki (existing Paths skipped)"

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, email, **options):
        try:
            owner = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            raise CommandError(f"No user with email {email}") from None
        created = skipped = 0
        for page_type, directory in okf.DIRS.items():
            for file in sorted((FIXTURES / directory).glob("*.md")):
                path = f"/{directory}/{file.name}"
                try:
                    services.insert_page(owner, path, page_type, file.read_text(encoding="utf-8"))
                except services.PathTaken:
                    skipped += 1
                except okf.OKFError as e:
                    raise CommandError(f"{path}: {e}") from e
                else:
                    created += 1
        self.stdout.write(f"created {created}, skipped {skipped}")
