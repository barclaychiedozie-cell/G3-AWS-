from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


class RoleBasedLoginView(auth_views.LoginView):
	template_name = "registration/login.html"

	def get_default_redirect_url(self):
		user = self.request.user

		if getattr(user, "is_superuser", False) or getattr(user, "role", "") == "admin":
			return str(reverse_lazy("admin:index"))
		if getattr(user, "role", "") == "clinician":
			return str(reverse_lazy("clinician_dashboard"))
		return str(reverse_lazy("dashboard"))
