from django.core.management.base import BaseCommand

from apps.schools.models import ClassLevel, School

CLASS_LEVELS = [
    {"name": "JSS 1", "order": 1},
    {"name": "JSS 2", "order": 2},
    {"name": "JSS 3", "order": 3},
    {"name": "SS 1", "order": 4},
    {"name": "SS 2", "order": 5},
    {"name": "SS 3", "order": 6},
]


class Command(BaseCommand):
    help = "Seed class levels (JSS 1-3, SS 1-3) for all schools"

    def add_arguments(self, parser):
        parser.add_argument("--school", type=str, help="Seed only for a specific school name")

    def handle(self, *args, **options):
        school_name = options.get("school")
        schools = School.objects.all()
        if school_name:
            schools = schools.filter(name__iexact=school_name)
            if not schools.exists():
                self.stderr.write(self.style.ERROR(f'School "{school_name}" not found'))
                return

        created_total = 0
        skipped_total = 0
        for school in schools:
            for level in CLASS_LEVELS:
                obj, created = ClassLevel.objects.get_or_create(
                    name=level["name"],
                    school=school,
                    defaults={"order": level["order"]},
                )
                if created:
                    created_total += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created "{level["name"]}" for {school.name}'))
                else:
                    skipped_total += 1
                    self.stdout.write(f'  Skipped "{level["name"]}" for {school.name} (already exists)')

        self.stdout.write(self.style.SUCCESS(f"\nDone: {created_total} created, {skipped_total} skipped"))
