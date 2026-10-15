from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import AccountStatus, UserRole
from apps.core.models import AuditEvent, AuditLog

from .helpers import ApiTestCase, make_user


def cookie_value(response):
    return response.cookies[settings.AUTH_COOKIE_NAME].value


class ProtectedAccessTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.me_url = reverse("accounts:me")

    def test_no_credentials(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "NOT_AUTHENTICATED")

    def test_valid_access_token(self):
        self.auth_as(self.user)
        self.assertEqual(self.client.get(self.me_url).status_code, 200)

    def test_expired_access_token(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(from_time=timezone.now() - timedelta(hours=1), lifetime=timedelta(minutes=1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "AUTHENTICATION_FAILED")
        self.assertEqual(response.json()["errors"], {})  # no token internals leaked

    def test_garbage_and_wrong_type_tokens(self):
        self.auth_as(self.user)
        for header in ("Bearer not.a.jwt", "Bearer ", "Basic abc"):
            self.client.credentials(HTTP_AUTHORIZATION=header)
            self.assertEqual(self.client.get(self.me_url).status_code, 401, header)

    def test_refresh_token_cannot_be_used_as_access_token(self):
        login = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {cookie_value(login)}")
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_suspension_takes_effect_immediately_on_existing_access_token(self):
        self.auth_as(self.user)
        self.user.status = AccountStatus.SUSPENDED
        self.user.save()
        self.assertEqual(self.client.get(self.me_url).status_code, 401)


class RefreshAndLogoutTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()

    def test_refresh_rotates_token_and_returns_new_access(self):
        login = self.login()
        old_cookie = cookie_value(login)
        response = self.post("refresh")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["access"])
        self.assertNotIn("refresh", response.json()["data"])
        self.assertNotEqual(cookie_value(response), old_cookie)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access']}")
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)

    def test_refresh_without_cookie(self):
        response = self.post("refresh")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "INVALID_REFRESH_TOKEN")

    def test_refresh_with_garbage_cookie(self):
        self.client.cookies[settings.AUTH_COOKIE_NAME] = "garbage"
        self.assertEqual(self.post("refresh").status_code, 401)

    def test_remember_me_choice_survives_rotation(self):
        self.login(remember_me=True)
        rotated = self.post("refresh").cookies[settings.AUTH_COOKIE_NAME]
        self.assertEqual(int(rotated["max-age"]), 30 * 24 * 3600)

    def test_reused_refresh_token_is_rejected_and_revokes_the_session_family(self):
        login = self.login()
        stolen = cookie_value(login)
        rotated = self.post("refresh")
        self.assertEqual(rotated.status_code, 200)

        # Attacker replays the already-used token.
        self.client.cookies[settings.AUTH_COOKIE_NAME] = stolen
        replay = self.post("refresh")
        self.assertEqual(replay.status_code, 401)

        # The legitimate newest token is now revoked as well.
        self.client.cookies[settings.AUTH_COOKIE_NAME] = cookie_value(rotated)
        self.assertEqual(self.post("refresh").status_code, 401)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditEvent.REFRESH_TOKEN_REUSE).exists())

    def test_expired_refresh_token_is_rejected(self):
        token = RefreshToken.for_user(self.user)
        token.set_exp(from_time=timezone.now() - timedelta(days=2), lifetime=timedelta(hours=1))
        self.client.cookies[settings.AUTH_COOKIE_NAME] = str(token)
        self.assertEqual(self.post("refresh").status_code, 401)

    def test_refresh_denied_once_account_is_suspended(self):
        self.login()
        self.user.status = AccountStatus.SUSPENDED
        self.user.save()
        self.assertEqual(self.post("refresh").status_code, 401)

    def test_logout_revokes_refresh_token_server_side(self):
        login = self.login()
        token = cookie_value(login)
        response = self.post("logout")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies[settings.AUTH_COOKIE_NAME].value, "")
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditEvent.LOGOUT).exists())

        # A copy of the token captured before logout no longer works.
        self.client.cookies[settings.AUTH_COOKIE_NAME] = token
        self.assertEqual(self.post("refresh").status_code, 401)

    def test_logout_is_idempotent_without_a_session(self):
        self.assertEqual(self.post("logout").status_code, 204)

    def test_refresh_and_logout_reject_untrusted_origin(self):
        self.login()
        for name in ("refresh", "logout"):
            self.assertEqual(self.post(name, HTTP_ORIGIN="https://evil.example").status_code, 403)
        self.assertEqual(BlacklistedToken.objects.count(), 0)

    def test_employer_role_comes_from_database_not_token(self):
        employer = make_user("hr@acme.example", role=UserRole.EMPLOYER)
        self.auth_as(employer)
        employer.role = UserRole.STUDENT
        employer.save()
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.json()["data"]["user"]["role"], "student")
