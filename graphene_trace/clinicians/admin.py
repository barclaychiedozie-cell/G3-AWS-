from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import ClinicianPatientAccess


# Requirement 4: Manage clinician access to patients
class ClinicianPatientAccessForm(forms.ModelForm):
    class Meta:
        model = ClinicianPatientAccess
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        clinician = cleaned.get('clinician')
        patient = cleaned.get('patient')
        if clinician and patient:
            qs = ClinicianPatientAccess.objects.filter(
                clinician=clinician, patient=patient
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f"An access record for {clinician} → {patient} already exists."
                )
        return cleaned


@admin.register(ClinicianPatientAccess)
class ClinicianPatientAccessAdmin(admin.ModelAdmin):
    form = ClinicianPatientAccessForm
    list_display = ('clinician', 'patient', 'assigned_at')
    search_fields = ('clinician__username', 'patient__username')
    list_filter = ('assigned_at',)
    ordering = ('-assigned_at',)
    actions = ['revoke_access']

    @admin.action(description='Revoke selected clinician access')
    def revoke_access(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} access assignment(s) revoked.')
