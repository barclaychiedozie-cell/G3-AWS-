from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create the default ajay superuser if it does not exist."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="ajay",
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "role": "admin",
            },
        )
        if created:
            user.set_password("ajay123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Superuser 'ajay' created."))
        else:
            self.stdout.write("Superuser 'ajay' already exists.")
