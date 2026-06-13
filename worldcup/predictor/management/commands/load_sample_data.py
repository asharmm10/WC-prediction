"""Management command to load sample data for the World Cup Prediction League."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Load sample data (participants and matches fixtures) and create "
        "a Django superuser (admin/admin123)."
    )

    def handle(self, *args, **options):
        # Load fixtures
        self.stdout.write("Loading participants fixture...")
        call_command("loaddata", "participants")
        self.stdout.write(self.style.SUCCESS("  Participants loaded."))

        self.stdout.write("Loading matches fixture...")
        call_command("loaddata", "matches")
        self.stdout.write(self.style.SUCCESS("  Matches loaded."))

        # Create superuser
        if User.objects.filter(username="admin").exists():
            self.stdout.write(
                self.style.WARNING("  Superuser 'admin' already exists — skipping.")
            )
        else:
            User.objects.create_superuser(
                username="admin",
                email="admin@worldcup2026.local",
                password="admin123",
            )
            self.stdout.write(self.style.SUCCESS("  Superuser 'admin' created (password: admin123)."))

        self.stdout.write(self.style.SUCCESS("\nSample data loaded successfully!"))
