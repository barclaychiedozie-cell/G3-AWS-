import csv

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from users.models import User
from .models import (
    Comment,
    Notification,
    PressureData,
    PressureUpload,
    HighPressureFlag,
    ClinicianPatientAccess,
)


class UploadPressureMatrixCSVForm(forms.Form):
    patient_username = forms.CharField(
        help_text="Existing patient username (role must be patient)."
    )
    timestamp = forms.CharField(
        required=False,
        help_text="Optional. ISO format like 2026-03-01T14:00:00Z. Leave blank to use now().",
    )
    csv_file = forms.FileField(
        help_text="Matrix CSV (no headers). Each cell is a pressure value."
    )


@admin.register(PressureUpload)
class PressureUploadAdmin(admin.ModelAdmin):
    list_display = ("patient", "timestamp", "uploaded_at", "rows", "cols", "csv_file")
    list_filter = ("patient",)
    search_fields = ("patient__username", "patient__email")
    ordering = ("-timestamp",)

    change_list_template = "admin/pressureupload_changelist.html"

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "upload-matrix-csv/",
                self.admin_site.admin_view(self.upload_matrix_csv),
                name="pressureupload_upload_matrix_csv",
            ),
        ]
        return custom + urls

    def upload_matrix_csv(self, request):
        if request.method == "POST":
            form = UploadPressureMatrixCSVForm(request.POST, request.FILES)
            if form.is_valid():
                patient_username = form.cleaned_data["patient_username"].strip()
                ts_raw = (form.cleaned_data.get("timestamp") or "").strip()
                f = form.cleaned_data["csv_file"]

                try:
                    patient = User.objects.get(username=patient_username)
                except User.DoesNotExist:
                    messages.error(request, f"User '{patient_username}' does not exist.")
                    return redirect("..")

                if getattr(patient, "role", None) != "patient":
                    messages.error(
                        request,
                        f"User '{patient_username}' exists but role is '{patient.role}', not 'patient'.",
                    )
                    return redirect("..")

                if ts_raw:
                    ts = parse_datetime(ts_raw) or parse_datetime(ts_raw.replace(" ", "T"))
                    if ts is None:
                        messages.error(request, f"Timestamp not parseable: {ts_raw}")
                        return redirect("..")
                    if timezone.is_naive(ts):
                        ts = timezone.make_aware(ts, timezone.get_current_timezone())
                else:
                    ts = timezone.now()

                rows, cols, encoding = self._count_matrix_dims_safe(f)

                try:
                    f.seek(0)
                except Exception:
                    pass

                upload = PressureUpload(
                    patient=patient,
                    timestamp=ts,
                    csv_file=f,
                    rows=rows,
                    cols=cols,
                )
                upload.save()

                messages.success(
                    request,
                    f"CSV stored for {patient.username} @ {ts.isoformat()} "
                    f"(rows={rows}, cols={cols}, encoding={encoding}).",
                )
                return redirect("..")
        else:
            form = UploadPressureMatrixCSVForm()

        return render(request, "admin/upload_pressure_matrix_csv.html", {"form": form})

    def _count_matrix_dims_safe(self, uploaded_file):
        raw = b"".join(uploaded_file.chunks())

        try:
            text = raw.decode("utf-8-sig", errors="replace")
            encoding = "utf-8-sig"
        except Exception:
            text = raw.decode("cp1252", errors="replace")
            encoding = "cp1252"

        reader = csv.reader(text.splitlines())
        rows = 0
        cols = 0
        for row in reader:
            if not row:
                continue
            rows += 1
            cols = max(cols, len(row))

        return rows, cols, encoding


@admin.register(PressureData)
class PressureDataAdmin(admin.ModelAdmin):
    list_display = ("patient", "timestamp", "sensor_location", "pressure_value")
    list_filter = ("sensor_location", "patient")
    search_fields = ("patient__username", "patient__email")
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "patient", "clinician", "is_reply", "text")
    list_filter = ("is_reply", "patient", "clinician")
    search_fields = ("patient__username", "clinician__username", "text")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "patient", "alert_level", "is_read", "message")
    list_filter = ("alert_level", "is_read", "patient")
    search_fields = ("patient__username", "message")


@admin.register(HighPressureFlag)
class HighPressureFlagAdmin(admin.ModelAdmin):
    list_display = ("patient", "start_time", "end_time", "max_pressure", "note")
    list_filter = ("patient",)
    search_fields = ("patient__username", "note")
    ordering = ("-start_time",)


@admin.register(ClinicianPatientAccess)
class ClinicianPatientAccessAdmin(admin.ModelAdmin):
    list_display = ("clinician", "patient", "created_at")
    list_filter = ("clinician", "patient")
    search_fields = ("clinician__username", "patient__username")
    ordering = ("-created_at",)

    # Add bulk actions for easier management
    actions = ['bulk_assign_patients', 'bulk_remove_assignments']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manage-access/', self.admin_site.admin_view(self.manage_access), name='manage_clinician_access'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist"""
        extra_context = extra_context or {}
        extra_context['manage_access_url'] = 'admin:manage_clinician_access'

        # Add summary statistics
        from django.db.models import Count
        clinician_stats = User.objects.filter(role='clinician').annotate(
            patient_count=Count('assigned_patients')
        ).order_by('-patient_count')[:10]  # Top 10 clinicians by patient count

        patient_count = User.objects.filter(role='patient').count()
        clinician_count = User.objects.filter(role='clinician').count()
        total_assignments = ClinicianPatientAccess.objects.count()

        extra_context.update({
            'clinician_stats': clinician_stats,
            'patient_count': patient_count,
            'clinician_count': clinician_count,
            'total_assignments': total_assignments,
        })

        return super().changelist_view(request, extra_context)

    def manage_access(self, request):
        """Custom view for managing clinician-patient access"""
        # Only allow admins to access this view
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage clinician access.")
            return redirect('admin:index')

        clinicians = User.objects.filter(role='clinician').prefetch_related('assigned_patients')
        patients = User.objects.filter(role='patient')

        if request.method == 'POST':
            clinician_id = request.POST.get('clinician_id')
            patient_ids = request.POST.getlist('patient_ids')

            if clinician_id and patient_ids:
                try:
                    clinician = User.objects.get(id=clinician_id, role='clinician')

                    # Remove existing assignments not in the selected list
                    ClinicianPatientAccess.objects.filter(
                        clinician=clinician
                    ).exclude(patient_id__in=patient_ids).delete()

                    # Add new assignments
                    for patient_id in patient_ids:
                        ClinicianPatientAccess.objects.get_or_create(
                            clinician=clinician,
                            patient_id=patient_id,
                            defaults={'created_at': timezone.now()}
                        )

                    messages.success(request, f"Updated patient assignments for {clinician.username}")
                    return redirect('admin:manage_clinician_access')
                except User.DoesNotExist:
                    messages.error(request, "Invalid clinician selected")

        context = {
            'title': 'Manage Clinician-Patient Access',
            'clinicians': clinicians,
            'patients': patients,
            'opts': self.model._meta,
        }
        return render(request, 'admin/manage_clinician_access.html', context)

    def bulk_assign_patients(self, request, queryset):
        """Bulk assign selected patients to a clinician"""
        if queryset.count() == 0:
            self.message_user(request, "No patients selected.", level=messages.WARNING)
            return

        # Get all clinicians for selection
        clinicians = User.objects.filter(role='clinician')
        if not clinicians.exists():
            self.message_user(request, "No clinicians available.", level=messages.ERROR)
            return

        if 'clinician_id' in request.POST:
            clinician_id = request.POST.get('clinician_id')
            try:
                clinician = User.objects.get(id=clinician_id, role='clinician')
                assigned_count = 0
                for access in queryset:
                    # Create assignment if it doesn't exist
                    ClinicianPatientAccess.objects.get_or_create(
                        clinician=clinician,
                        patient=access.patient,
                        defaults={'created_at': timezone.now()}
                    )
                    assigned_count += 1
                self.message_user(request, f"Assigned {assigned_count} patients to {clinician.username}.")
            except User.DoesNotExist:
                self.message_user(request, "Invalid clinician selected.", level=messages.ERROR)
        else:
            # Show form to select clinician
            return render(request, 'admin/bulk_assign_patients.html', {
                'title': 'Bulk Assign Patients to Clinician',
                'patients': [access.patient for access in queryset],
                'clinicians': clinicians,
                'action': 'bulk_assign_patients',
            })

    bulk_assign_patients.short_description = "Assign selected patients to a clinician"

    def bulk_remove_assignments(self, request, queryset):
        """Bulk remove selected assignments"""
        deleted_count = queryset.delete()[0]
        self.message_user(request, f"Removed {deleted_count} clinician-patient assignments.")

    bulk_remove_assignments.short_description = "Remove selected assignments"