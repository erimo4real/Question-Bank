from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

PASSWORDS = {
    "superadmin@example.com": "superadmin123",
    "admin@greenfieldacademy.com": "admin123",
    "teacher@greenfieldacademy.com": "teacher123",
    "admin@abccollage.com": "admin123",
    "teacher@abccollage.com": "teacher123",
}


class Command(BaseCommand):
    help = "Force-reset all known passwords and verify DB connectivity"

    def handle(self, *args, **options):
        total = User.objects.count()
        self.stdout.write(f"  Total users in DB: {total}")

        for email, pw in PASSWORDS.items():
            try:
                u = User.objects.get(email=email)
                u.set_password(pw)
                u.save()
                verified = u.check_password(pw)
                self.stdout.write(self.style.SUCCESS(
                    f"  Reset + verified: {email} | check_password={verified}"
                ))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  NOT FOUND: {email}"))
