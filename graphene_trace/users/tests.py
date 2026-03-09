from django.test import TestCase
from django.urls import reverse

from .models import User


class LogoutUserStoryTests(TestCase):
	def test_patient_clinician_and_admin_can_logout(self):
		logout_url = reverse("logout")
		login_url = reverse("login")

		roles = ["patient", "clinician", "admin"]

		for role in roles:
			with self.subTest(role=role):
				user = User.objects.create_user(
					username=f"{role}_user",
					password="TestPass123!",
					role=role,
				)
				self.client.force_login(user)

				response = self.client.post(logout_url, follow=False)

				self.assertEqual(response.status_code, 302)
				self.assertEqual(response.url, login_url)
				self.assertNotIn("_auth_user_id", self.client.session)
