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
        PressureData,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    is_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        who = self.clinician.username if self.clinician else self.patient.username
        return f"{who}: {self.text[:30]}"


class Notification(models.Model):
    ALERT_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    alert_level = models.CharField(
        max_length=20,
        choices=ALERT_CHOICES,
        default="info",
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.patient.username}: {self.alert_level} - {self.message[:40]}"


class HighPressureFlag(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pressure_flags",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_pressure = models.FloatField()
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return (
            f"{self.patient.username} high pressure from "
            f"{self.start_time} to {self.end_time}"
        )


class ClinicianPatientAccess(models.Model):
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_patients",
        limit_choices_to={"role": "clinician"},
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_clinicians",
        limit_choices_to={"role": "patient"},
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("clinician", "patient")

    def __str__(self):
        return f"{self.clinician.username} -> {self.patient.username}"


class PatientStatus(models.Model):
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_status",
    )
    high_priority = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Status"
        verbose_name_plural = "Patient Statuses"

    def __str__(self):
        priority = "High Priority" if self.high_priority else "Normal"
        return f"{self.patient.username} - {priority}"


class SessionSummary(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_summaries",
    )
    session_date = models.DateTimeField(default=timezone.now)
    duration_minutes = models.PositiveIntegerField(default=0)
    pressure_score = models.FloatField(default=0)
    posture_status = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-session_date"]

    def __str__(self):
        return (
            f"{self.patient.username} - "
            f"Score: {self.pressure_score} - "
            f"{self.session_date}"
        )