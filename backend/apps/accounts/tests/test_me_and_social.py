from django.urls import reverse

from apps.accounts.models import UserRole

from .helpers import ApiTestCase, make_user


class MeEndpointTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice@example.com")
        self.bob = make_user("bob@example.com")
        self.url = reverse("accounts:me")

    def test_returns_safe_profile_of_authenticated_user(self):
        self.auth_as(self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        user = response.json()["data"]["user"]
        self.assertEqual(set(user), {"id", "email", "role", "status", "profile"})
        self.assertEqual(user["email"], "alice@example.com")
        self.assertEqual(user["profile"], {"first_name": "Test", "last_name": "Student"})
        for secret in ("password", "last_login", "is_staff", "is_superuser"):
            self.assertNotIn(secret, response.content.decode())

    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_user_id_in_request_is_ignored(self):
        """IDOR: /me/ can only ever return the caller, whatever the client sends."""
        self.auth_as(self.alice)
        for suffix in (f"?id={self.bob.id}", f"?user_id={self.bob.id}", f"?email={self.bob.email}"):
            response = self.client.get(self.url + suffix, HTTP_X_USER_ID=str(self.bob.id))
            self.assertEqual(response.json()["data"]["user"]["email"], "alice@example.com")

    def test_me_has_no_id_variant_and_rejects_writes(self):
        self.auth_as(self.alice)
        self.assertEqual(self.client.get(f"{self.url}{self.bob.id}/").status_code, 404)
        self.assertEqual(
            self.client.post(self.url, {"email": "x@example.com"}, format="json").status_code, 405
        )
        self.assertEqual(
            self.client.patch(self.url, {"role": "administrator"}, format="json").status_code, 405
        )

    def test_employer_and_staff_roles_serialise_profiles(self):
        make_user("hr@acme.example", role=UserRole.EMPLOYER)
        make_user("mod@example.com", role=UserRole.MODERATOR)
        self.auth_as(make_user("mod2@example.com", role=UserRole.MODERATOR))
        self.assertIsNone(self.client.get(self.url).json()["data"]["user"]["profile"])


class SocialLoginTests(ApiTestCase):
    def test_not_configured_providers_return_501(self):
        for provider in ("google", "facebook"):
            response = self.client.post(
                reverse("accounts:social-login", args=[provider]), {}, format="json"
            )
            self.assertEqual(response.status_code, 501)
            self.assertEqual(response.json()["code"], "NOT_IMPLEMENTED")

    def test_unknown_provider_404(self):
        response = self.client.post(
            reverse("accounts:social-login", args=["myspace"]), {}, format="json"
        )
        self.assertEqual(response.status_code, 404)
