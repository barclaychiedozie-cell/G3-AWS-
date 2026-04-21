from django.db import models
from django.conf import settings

class ClinicianPatientAccess(models.Model):
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_patients',
        limit_choices_to={'role': 'clinician'},
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_clinicians',
        limit_choices_to={'role': 'patient'},
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('clinician', 'patient')
        verbose_name = 'Clinician Assignment'
        verbose_name_plural = 'Clinician Assignments'

    def __str__(self):
        return f'{self.clinician.username} -> {self.patient.username}'
