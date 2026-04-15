"""
URL configuration for graphene_trace project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
<<<<<<< HEAD
from django.views.generic import RedirectView
from users.views import RoleBasedLoginView, role_home_redirect
=======
from django.conf import settings
from django.conf.urls.static import static
>>>>>>> 0741e6e60f08aeb22abba00e3256829320db8944

urlpatterns = [
    path("admin/", admin.site.urls),

    # Backward-compatible aliases
    path("login", RedirectView.as_view(url="/accounts/login/", permanent=False)),
    path("login/", RedirectView.as_view(url="/accounts/login/", permanent=False)),

    # Users app URLs (register, etc.)
    path("accounts/", include("users.urls")),

    # Auth (login/logout) - keep your existing behavior
    path(
        "accounts/login/",
        RoleBasedLoginView.as_view(),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="/accounts/login/"),
        name="logout",
    ),

    # Password reset flow (Forgot password)
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    path("", role_home_redirect, name="home"),
    path("", include("patients.urls")),
    path("", include("clinicians.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)