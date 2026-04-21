from django.contrib import admin
from django.contrib.auth.models import Group

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# Admin site branding
admin.site.site_header = "Graphene Trace Administration"
admin.site.site_title = "Graphene Trace Admin"
admin.site.index_title = "Site Administration"
