import csv
import io

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import PressureUpload, PressureData, Comment, Message, Notification


ALLOWED_CSV_CONTENT_TYPES = {'text/csv', 'application/vnd.ms-excel', 'text/plain'}


# Requirement 5: Upload patient data
class PressureUploadForm(forms.ModelForm):
    class Meta:
        model = PressureUpload
        exclude = ('rows', 'cols')

    def clean_csv_file(self):
        f = self.cleaned_data.get('csv_file')
        if not f:
            return f
        # Requirement 5.4: reject non-CSV by extension
        if not f.name.lower().endswith('.csv'):
            raise ValidationError("Only .csv files are accepted.")
        # Requirement 5.4: reject non-CSV by MIME type
        content_type = getattr(f, 'content_type', '')
        if content_type and content_type not in ALLOWED_CSV_CONTENT_TYPES:
            raise ValidationError(f"Invalid file type '{content_type}'. Only CSV files are accepted.")
        # Requirement 5.5: reject empty files
        if f.size == 0:
            raise ValidationError("The uploaded CSV file is empty.")
        return f

    def clean_patient(self):
        # Requirement 5.3: reject non-patient users
        patient = self.cleaned_data.get('patient')
        if patient and getattr(patient, 'role', None) != 'patient':
            raise ValidationError(
                f"'{patient.username}' is not a patient. Only users with role 'patient' can have data uploaded."
            )
        return patient


@admin.register(PressureUpload)
class PressureUploadAdmin(admin.ModelAdmin):
    form = PressureUploadForm
    list_display = ('patient', 'timestamp', 'uploaded_at', 'rows', 'cols', 'csv_file')
    search_fields = ('patient__username',)
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)

    def save_model(self, request, obj, form, change):
        csv_file = form.cleaned_data.get('csv_file')
        if csv_file:
            csv_file.seek(0)
            text = io.TextIOWrapper(csv_file, encoding='utf-8', errors='replace')
            reader = csv.reader(text)
            row_list = list(reader)
            if not row_list:
                raise ValidationError("The uploaded CSV file is empty.")
            # Requirement 5.6: record rows and cols metadata
            obj.rows = len(row_list)
            obj.cols = max(len(r) for r in row_list) if row_list else 0
        super().save_model(request, obj, form, change)


@admin.register(PressureData)
class PressureDataAdmin(admin.ModelAdmin):
    list_display = ('patient', 'sensor_location', 'pressure_value', 'timestamp')
    search_fields = ('patient__username', 'sensor_location')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'clinician', 'text', 'timestamp', 'is_reply')
    search_fields = ('patient__username', 'clinician__username', 'text')
    list_filter = ('is_reply', 'timestamp')
    ordering = ('-timestamp',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'timestamp', 'is_read')
    search_fields = ('sender__username', 'receiver__username')
    list_filter = ('is_read', 'timestamp')
    ordering = ('-timestamp',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'message', 'timestamp', 'is_read')
    search_fields = ('patient__username',)
    list_filter = ('is_read', 'timestamp')
    ordering = ('-timestamp',)
