from django.contrib import admin
from .models import PressureUpload

@admin.register(PressureUpload)
class PressureUploadAdmin(admin.ModelAdmin):
    exclude = ('rows', 'cols')
