from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("patient", "Patient"),
        ("clinician", "Clinician"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    high_priority = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = "admin"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
