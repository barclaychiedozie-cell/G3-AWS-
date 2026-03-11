import csv

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from users.models import User
from .models import Comment, Notification, PressureData, PressureUpload


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

                # patient lookup
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

                # timestamp
                if ts_raw:
                    ts = parse_datetime(ts_raw) or parse_datetime(ts_raw.replace(" ", "T"))
                    if ts is None:
                        messages.error(request, f"Timestamp not parseable: {ts_raw}")
                        return redirect("..")
                    if timezone.is_naive(ts):
                        ts = timezone.make_aware(ts, timezone.get_current_timezone())
                else:
                    ts = timezone.now()

                # IMPORTANT: compute dims without wrapping/closing f.file (fixes Windows temp-file FileNotFoundError)
                rows, cols, encoding = self._count_matrix_dims_safe(f)

                # Rewind so FileField can save correctly
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
        """
        Safely compute rows/cols without touching uploaded_file.file / TextIOWrapper,
        which can close the underlying Windows temp file and break FileField save().
        """
        raw = b"".join(uploaded_file.chunks())

        # Try utf-8-sig first, then fallback to cp1252
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
    list_display = ("timestamp", "patient", "is_read", "message")
    list_filter = ("is_read", "patient")
    search_fields = ("patient__username", "message")