import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import AccountStatus, SocialAccount, StudentProfile, User
from apps.accounts.social import GoogleVerifier, SocialAuthError, SocialIdentity
from apps.core.models import AuditEvent, AuditLog

from .helpers import ApiTestCase, make_user

GOOGLE_ID = "test-client-id.apps.googleusercontent.com"


def identity(**overrides):
    values = {
        "provider": "google",
        "subject": "google-sub-1",
        "email": "gina@gmail.example",
        "first_name": "Gina",
        "last_name": "Jalloh",
    }
    values.update(overrides)
    return SocialIdentity(**values)


@override_settings(GOOGLE_OAUTH_CLIENT_ID=GOOGLE_ID)
class GoogleLoginTests(ApiTestCase):
    def google(self, ident=None, **payload):
        body = {"credential": "fake-id-token", **payload}
        with mock.patch.object(GoogleVerifier, "verify", return_value=ident or identity()):
            return self.client.post(
                reverse("accounts:social-login", args=["google"]), body, format="json"
            )

    def test_providers_lists_google_only_when_configured(self):
        url = reverse("accounts:providers")
        data = self.client.get(url).json()["data"]
        self.assertEqual(data, {"google": {"client_id": GOOGLE_ID}, "facebook": None})
        with override_settings(GOOGLE_OAUTH_CLIENT_ID=""):
            self.assertIsNone(self.client.get(url).json()["data"]["google"])

    def test_new_user_requires_terms(self):
        response = self.google(terms_accepted=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "TERMS_REQUIRED")
        self.assertEqual(User.objects.count(), 0)

    def test_first_sign_in_creates_student_and_logs_in(self):
        response = self.google(terms_accepted=True)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["access"])
        self.assertEqual(data["user"]["role"], "student")
        self.assertEqual(data["user"]["profile"], {"first_name": "Gina", "last_name": "Jalloh"})
        self.assertIn(settings.AUTH_COOKIE_NAME, response.cookies)

        user = User.objects.get(email="gina@gmail.example")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(SocialAccount.objects.filter(user=user, subject="google-sub-1").exists())
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())
        self.assertTrue(user.legal_acceptances.exists())

        # The issued access token really works.
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)

    def test_returning_user_logs_in_without_terms(self):
        self.google(terms_accepted=True)
        response = self.google()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(event_type=AuditEvent.LOGIN_SUCCESS).count(), 2)

    def test_existing_password_account_is_not_auto_linked(self):
        make_user("gina@gmail.example")
        response = self.google(terms_accepted=True)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "ACCOUNT_EXISTS")
        self.assertFalse(SocialAccount.objects.exists())
        self.assertNotIn(settings.AUTH_COOKIE_NAME, response.cookies)

    def test_suspended_social_user_is_rejected(self):
        self.google(terms_accepted=True)
        User.objects.update(status=AccountStatus.SUSPENDED)
        self.assertEqual(self.google().status_code, 401)

    def test_invalid_google_token_is_rejected(self):
        with mock.patch(
            "apps.accounts.social.id_token.verify_oauth2_token", side_effect=ValueError("bad")
        ):
            response = self.client.post(
                reverse("accounts:social-login", args=["google"]),
                {"credential": "forged", "terms_accepted": True},
                format="json",
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "SOCIAL_AUTH_FAILED")
        self.assertEqual(User.objects.count(), 0)

    def test_unverified_google_email_is_rejected(self):
        claims = {"sub": "1", "email": "x@gmail.example", "email_verified": False}
        with mock.patch("apps.accounts.social.id_token.verify_oauth2_token", return_value=claims):
            with self.assertRaises(SocialAuthError):
                GoogleVerifier(GOOGLE_ID).verify("token")

    def test_verifier_receives_our_client_id_as_audience(self):
        claims = {"sub": "1", "email": "X@Gmail.example", "email_verified": True, "given_name": "X"}
        with mock.patch(
            "apps.accounts.social.id_token.verify_oauth2_token", return_value=claims
        ) as verify:
            result = GoogleVerifier(GOOGLE_ID).verify("token")
        self.assertEqual(verify.call_args.args[2], GOOGLE_ID)
        self.assertEqual(result.email, "x@gmail.example")

    def test_untrusted_origin_rejected(self):
        response = self.client.post(
            reverse("accounts:social-login", args=["google"]),
            {"credential": "t"},
            format="json",
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)

    def test_not_configured_returns_501(self):
        with override_settings(GOOGLE_OAUTH_CLIENT_ID=""):
            response = self.client.post(
                reverse("accounts:social-login", args=["google"]),
                {"credential": "t"},
                format="json",
            )
        self.assertEqual(response.status_code, 501)


class SameOriginTests(ApiTestCase):
    def test_own_origin_is_allowed_even_if_not_in_cors_list(self):
        make_user()
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "student@example.com", "password": "Tr1cky-Horse-Battery-92"},
            format="json",
            HTTP_ORIGIN="http://testserver",
        )
        self.assertEqual(response.status_code, 200)


class SpaServingTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dist = Path(tempfile.mkdtemp())
        (self.dist / "index.html").write_text("<!doctype html><div id=root></div>")
        (self.dist / "assets").mkdir()
        override = override_settings(FRONTEND_DIST_DIR=self.dist)
        override.enable()
        self.addCleanup(override.disable)

    def test_client_routes_get_index_html_uncached(self):
        for path in ("/", "/login", "/register", "/dashboard/deep/link"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b"id=root", response.content)
            self.assertEqual(response["Cache-Control"], "no-cache")

    def test_missing_asset_is_a_real_404_not_html(self):
        response = self.client.get("/assets/index-deadbeef.js")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"id=root", response.content)

    def test_api_unknown_path_is_json_404(self):
        response = self.client.get("/api/v1/nope/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "NOT_FOUND")

    def test_post_to_spa_route_not_allowed(self):
        self.assertEqual(self.client.post("/login").status_code, 405)

    def test_clear_message_when_frontend_not_built(self):
        with override_settings(FRONTEND_DIST_DIR=self.dist / "missing"):
            self.assertEqual(self.client.get("/").status_code, 503)
