import csv
from io import TextIOWrapper

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from users.models import User
from .models import Comment, Notification, PressureData


class UploadPressureMatrixCSVForm(forms.Form):
    patient_username = forms.CharField(help_text="Existing patient username (role must be patient).")
    timestamp = forms.CharField(
        required=False,
        help_text="Optional. ISO format like 2026-03-01T14:00:00Z. Leave blank to use now().",
    )
    csv_file = forms.FileField(
        help_text="Matrix CSV (no headers). Each cell is a pressure value."
    )


@admin.register(PressureData)
class PressureDataAdmin(admin.ModelAdmin):
    list_display = ("patient", "timestamp", "sensor_location", "pressure_value")
    list_filter = ("sensor_location", "patient")
    search_fields = ("patient__username", "patient__email")
    ordering = ("-timestamp",)

    change_list_template = "admin/pressuredata_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "upload-matrix-csv/",
                self.admin_site.admin_view(self.upload_matrix_csv),
                name="pressuredata_upload_matrix_csv",
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
                    ts = parse_datetime(ts_raw)
                    if ts is None:
                        ts = parse_datetime(ts_raw.replace(" ", "T"))
                    if ts is None:
                        messages.error(request, f"Timestamp not parseable: {ts_raw}")
                        return redirect("..")
                else:
                    ts = timezone.now()

                created, errors = self._import_matrix_csv(patient=patient, timestamp=ts, uploaded_file=f)

                for e in errors[:30]:
                    messages.error(request, e)
                if len(errors) > 30:
                    messages.error(request, f"... plus {len(errors) - 30} more errors")

                messages.success(
                    request,
                    f"Matrix import complete for {patient.username} @ {ts.isoformat()}: "
                    f"created={created}, errors={len(errors)}",
                )
                return redirect("..")
        else:
            form = UploadPressureMatrixCSVForm()

        return render(request, "admin/upload_pressure_matrix_csv.html", {"form": form})

    def _import_matrix_csv(self, patient, timestamp, uploaded_file):
        created = 0
        errors = []

        wrapper = TextIOWrapper(uploaded_file.file, encoding="utf-8")
        reader = csv.reader(wrapper)

        rows_to_create = []

        # NOTE: we use 1-based r/c to match your parsing: r(\d+)_c(\d+)
        for r_index, row in enumerate(reader, start=1):
            if not row:
                continue

            for c_index, cell in enumerate(row, start=1):
                raw = (cell or "").strip()

                # allow empty cells as 0
                if raw == "":
                    val = 0.0
                else:
                    try:
                        val = float(raw)
                    except ValueError:
                        errors.append(f"Bad number at r{r_index} c{c_index}: '{raw}'")
                        continue

                rows_to_create.append(
                    PressureData(
                        patient=patient,
                        timestamp=timestamp,
                        sensor_location=f"r{r_index}_c{c_index}",
                        pressure_value=val,
                    )
                )

        if rows_to_create:
            PressureData.objects.bulk_create(rows_to_create, batch_size=5000)
            created = len(rows_to_create)

        return created, errors


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