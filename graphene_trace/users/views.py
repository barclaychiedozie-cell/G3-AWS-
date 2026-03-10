from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.shortcuts import redirect


class RoleBasedLoginView(auth_views.LoginView):
	template_name = "registration/login.html"

	def get_default_redirect_url(self):
		user = self.request.user

		if getattr(user, "is_superuser", False) or getattr(user, "role", "") == "admin":
			return str(reverse_lazy("admin:index"))
		if getattr(user, "role", "") == "clinician":
			return str(reverse_lazy("clinician_dashboard"))
		return str(reverse_lazy("dashboard"))


def role_home_redirect(request):
	if not request.user.is_authenticated:
		return redirect("login")

	if getattr(request.user, "is_superuser", False) or getattr(request.user, "role", "") == "admin":
		return redirect("admin:index")
	if getattr(request.user, "role", "") == "clinician":
		return redirect("clinician_dashboard")
	return redirect("dashboard")
