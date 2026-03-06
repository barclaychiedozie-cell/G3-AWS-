from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [("patient", "Patient"), ("clinician", "Clinician")]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")

    # IMPORTANT:
    # - null=True avoids UNIQUE conflicts during migration on SQLite (multiple NULLs allowed)
    # - keep unique=True to guarantee no duplicates once filled
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username