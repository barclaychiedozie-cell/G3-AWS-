from django.db import models
from django.conf import settings
from django.utils import timezone


class PressureData(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pressure_data")
    timestamp = models.DateTimeField(default=timezone.now)
    pressure_value = models.FloatField()
    sensor_location = models.CharField(max_length=50)  # e.g. "r3_c7" or "left_hip"

    class Meta:
        ordering = ["-timestamp"]


# ADD this below PressureData in the same file

class Comment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinician_comments")
    pressure_data = models.ForeignKey(PressureData, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    is_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]