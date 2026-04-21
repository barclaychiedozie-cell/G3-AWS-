from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    ClinicianAccessManagement,
    UserRoleAssignment,
    UserAccountManagement,
    PatientDataUpload,
)


# ── Requirement 2: Manage clinician access to patients ────────────────────────
@admin.register(ClinicianAccessManagement)
class ClinicianAccessManagementAdmin(admin.ModelAdmin):
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


# ── Requirement 3: Assign roles ───────────────────────────────────────────────
@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('role',)
    fields = ('username', 'role')
    readonly_fields = ('username',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ── Requirement 4: Create and manage user accounts ────────────────────────────
@admin.register(UserAccountManagement)
class UserAccountManagementAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['activate_users', 'deactivate_users']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Access', {'fields': ('role', 'id_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'is_active'),
        }),
    )

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)


# ── Requirement 5: Upload patient data ────────────────────────────────────────
@admin.register(PatientDataUpload)
class PatientDataUploadAdmin(admin.ModelAdmin):
    list_display = ('patient', 'timestamp', 'uploaded_at', 'csv_file')
    search_fields = ('patient__username',)
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)
    exclude = ('rows', 'cols')
