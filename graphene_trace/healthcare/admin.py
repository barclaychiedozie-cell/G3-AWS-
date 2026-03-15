from django.contrib import admin
from .models import Patient, Clinician


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'medical_record_number', 'email', 'phone', 'age', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'medical_record_number']
    list_filter = ['created_at', 'date_of_birth']
    readonly_fields = ['age']


@admin.register(Clinician)
class ClinicianAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'specialty', 'license_number', 'email', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'license_number', 'specialty']
    list_filter = ['specialty', 'is_active', 'created_at']
