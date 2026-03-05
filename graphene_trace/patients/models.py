from django.db import models
from django.conf import settings
from django.utils import timezone


class PressureData(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pressure_data",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    pressure_value = models.FloatField()
    sensor_location = models.CharField(max_length=50)  # e.g. "r3_c7"

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.patient.username} {self.sensor_location} {self.pressure_value} @ {self.timestamp}"


class Comment(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinician_comments",
    )
    pressure_data = models.ForeignKey(PressureData, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    is_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        who = self.clinician.username if self.clinician else self.patient.username
        return f"{who}: {self.text[:30]}"


class Notification(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.patient.username}: {self.message[:40]}"