from datetime import timezone as dt_timezone

from django.conf import settings
from django.db import models
from django.utils import timezone


def patient_pressure_upload_path(instance, filename: str) -> str:
    """
    MEDIA_ROOT path for CSV uploads.

    Example:
      pressure_uploads/patient_12/2026/03/10/20260310T083522Z_matrix.csv
    """
    ts = instance.timestamp or timezone.now()
    ts_utc = ts.astimezone(dt_timezone.utc)

    safe_name = filename.replace("\\", "/").split("/")[-1]
    return (
        f"pressure_uploads/patient_{instance.patient_id}/"
        f"{ts_utc:%Y/%m/%d}/"
        f"{ts_utc:%Y%m%dT%H%M%SZ}_{safe_name}"
    )


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
        return (
            f"{self.patient.username} {self.sensor_location} "
            f"{self.pressure_value} @ {self.timestamp}"
        )


class PressureUpload(models.Model):
    """
    File-based upload for past records.

    Stores the CSV file on disk (MEDIA_ROOT) and stores only a reference/path in DB.
    The patient dashboard loads past heatmaps by reading this file.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pressure_uploads",
    )
    timestamp = models.DateTimeField(
        help_text="The timestamp associated with this grid snapshot / upload."
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    csv_file = models.FileField(upload_to=patient_pressure_upload_path)

    # Optional metadata for faster UI (can be 0 if unknown)
    rows = models.PositiveIntegerField(default=0)
    cols = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["patient", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.patient.username} upload @ {self.timestamp}"


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
    pressure_data = models.ForeignKey(
        PressureData, on_delete=models.CASCADE, null=True, blank=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    is_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        who = self.clinician.username if self.clinician else self.patient.username
        return f"{who}: {self.text[:30]}"


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["sender", "receiver", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:30]}"


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