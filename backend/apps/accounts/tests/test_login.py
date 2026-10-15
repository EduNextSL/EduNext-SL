from unittest import mock

from django.conf import settings

from apps.accounts.models import AccountStatus, UserRole
from apps.core.models import AuditEvent, AuditLog
from apps.core.throttling import LoginIdentityThrottle, LoginThrottle

from .helpers import STRONG_PASSWORD, ApiTestCase, make_user


class LoginTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()

    def test_valid_credentials(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["access"])
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["user"]["email"], "student@example.com")
        self.assertNotIn("refresh", data)  # refresh token is cookie-only
        self.assertNotIn("password", str(response.json()))

        cookie = response.cookies[settings.AUTH_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], settings.AUTH_COOKIE_SAMESITE)
        self.assertEqual(cookie["path"], settings.AUTH_COOKIE_PATH)

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditEvent.LOGIN_SUCCESS).exists())

    def test_email_login_is_case_insensitive(self):
        self.assertEqual(self.login(email="  STUDENT@Example.com ").status_code, 200)

    def test_remember_me_controls_cookie_persistence(self):
        persistent = self.login(remember_me=True).cookies[settings.AUTH_COOKIE_NAME]
        self.assertEqual(int(persistent["max-age"]), 30 * 24 * 3600)
        session = self.login(remember_me=False).cookies[settings.AUTH_COOKIE_NAME]
        self.assertEqual(session["max-age"], "")

    def test_wrong_password_and_unknown_email_look_identical(self):
        wrong = self.login(password="Wrong-Password-123")
        unknown = self.login(email="nobody@example.com")
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(wrong.json(), unknown.json())
        self.assertEqual(wrong.json()["code"], "INVALID_CREDENTIALS")
        self.assertNotIn(settings.AUTH_COOKIE_NAME, wrong.cookies)
        self.assertEqual(AuditLog.objects.filter(event_type=AuditEvent.LOGIN_FAILURE).count(), 2)

    def test_non_active_accounts_get_the_same_generic_failure(self):
        reference = self.login(password="Wrong-Password-123").json()
        for status in (AccountStatus.SUSPENDED, AccountStatus.DISABLED, AccountStatus.PENDING):
            self.user.status = status
            self.user.save()
            response = self.login()
            self.assertEqual(response.status_code, 401, status)
            self.assertEqual(response.json(), reference)

    def test_inactive_flag_blocks_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 401)

    def test_missing_fields(self):
        response = self.post("login", {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "VALIDATION_ERROR")

    def test_ip_throttle(self):
        with mock.patch.dict(LoginThrottle.THROTTLE_RATES, {"login": "3/minute"}):
            codes = [self.login(email=f"u{i}@example.com").status_code for i in range(5)]
        self.assertEqual(codes[:3], [401, 401, 401])
        self.assertEqual(codes[3:], [429, 429])

    def test_throttled_response_uses_standard_error_shape(self):
        with mock.patch.dict(LoginThrottle.THROTTLE_RATES, {"login": "1/minute"}):
            self.login()
            response = self.login()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["code"], "THROTTLED")
        self.assertIn("Retry-After", response)

    def test_per_email_throttle_applies_across_changing_ips(self):
        with mock.patch.dict(LoginIdentityThrottle.THROTTLE_RATES, {"login_identity": "2/minute"}):
            codes = [self.login(password="Bad-Password-123").status_code for _ in range(3)]
        self.assertEqual(codes, [401, 401, 429])

    def test_cross_origin_login_from_untrusted_origin_is_rejected(self):
        response = self.post(
            "login",
            {"email": "student@example.com", "password": STRONG_PASSWORD},
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(settings.AUTH_COOKIE_NAME, response.cookies)

    def test_trusted_origin_is_accepted(self):
        response = self.post(
            "login",
            {"email": "student@example.com", "password": STRONG_PASSWORD},
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, 200)

    def test_employer_login_returns_company_profile(self):
        make_user("hr@acme.example", role=UserRole.EMPLOYER)
        response = self.login("hr@acme.example")
        self.assertEqual(response.json()["data"]["user"]["profile"]["name"], "Acme")
