from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import StudentProfile, User, UserRole
from apps.companies.models import Company

STRONG_PASSWORD = "Tr1cky-Horse-Battery-92"
NEW_PASSWORD = "Another-Str0ng-Passphrase-7"


def make_user(
    email="student@example.com", role=UserRole.STUDENT, password=STRONG_PASSWORD, **extra
):
    user = User.objects.create_user(email=email, password=password, role=role, **extra)
    if role == UserRole.STUDENT:
        StudentProfile.objects.create(user=user, first_name="Test", last_name="Student")
    elif role == UserRole.EMPLOYER:
        Company.objects.create(
            owner=user, name="Acme", contact_full_name="Ann Acme", work_email=user.email
        )
    return user


def student_payload(**overrides):
    payload = {
        "first_name": "Aminata",
        "last_name": "Kamara",
        "email": "aminata@example.com",
        "password": STRONG_PASSWORD,
        "password_confirm": STRONG_PASSWORD,
        "terms_accepted": True,
    }
    payload.update(overrides)
    return payload


def company_payload(**overrides):
    payload = {
        "company_name": "Salone Tech Ltd",
        "contact_full_name": "Mohamed Bangura",
        "work_email": "hr@salonetech.example",
        "password": STRONG_PASSWORD,
        "password_confirm": STRONG_PASSWORD,
        "terms_accepted": True,
    }
    payload.update(overrides)
    return payload


class ApiTestCase(APITestCase):
    """Fresh cache (throttle counters) per test and a JSON client."""

    client_class = APIClient

    def setUp(self):
        super().setUp()
        cache.clear()

    def post(self, name, data=None, **extra):
        return self.client.post(reverse(f"accounts:{name}"), data or {}, format="json", **extra)

    def login(self, email="student@example.com", password=STRONG_PASSWORD, remember_me=False):
        return self.post(
            "login", {"email": email, "password": password, "remember_me": remember_me}
        )

    def auth_as(self, user, password=STRONG_PASSWORD):
        """Log in through the API and set the Bearer header; returns the login response."""
        response = self.login(user.email, password)
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access']}")
        return response
