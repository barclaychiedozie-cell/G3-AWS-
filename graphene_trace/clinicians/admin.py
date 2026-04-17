from django.contrib import admin
from .models import ClinicianPatientAccess

@admin.register(ClinicianPatientAccess)
class ClinicianPatientAccessAdmin(admin.ModelAdmin):
    list_display = ('clinician', 'patient', 'assigned_at')
    search_fields = ('clinician__username', 'patient__username')
    list_filter = ('assigned_at',)
