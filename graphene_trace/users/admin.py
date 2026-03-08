from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Admin for the custom users.User model.

    Provides:
      - Add/change/delete users
      - Password reset/change UI (via Django's built-in UserAdmin)
    """

    ordering = ("username",)
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")

    # If you use a lot of users, this is faster than a dropdown in related models
    # (safe to keep even if small)
    # raw_id_fields = ()

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Role"), {"fields": ("role",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "role", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )