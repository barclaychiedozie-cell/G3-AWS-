from django.contrib import admin
from django.contrib.auth.models import Group

# Remove Groups from admin
admin.site.unregister(Group)
