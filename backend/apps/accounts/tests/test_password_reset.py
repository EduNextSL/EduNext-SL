import uuid
from datetime import timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.accounts.models import AccountStatus, User
from apps.core.models import AuditEvent, AuditLog
from apps.core.throttling import PasswordResetRequestThrottle

from .helpers import NEW_PASSWORD, STRONG_PASSWORD, ApiTestCase, make_user


def extract_link_params(message):
    link = next(line for line in message.body.splitlines() if line.startswith("http"))
    query = parse_qs(urlparse(link).query)
    return query["uid"][0], query["token"][0]


class PasswordResetTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()

    def request_reset(self, email="student@example.com"):
        return self.post("password-reset-request", {"email": email})

    def confirm(self, uid, token, password=NEW_PASSWORD, confirm=None):
        return self.post(
            "password-reset-confirm",
            {
                "uid": uid,
                "token": token,
                "new_password": password,
                "new_password_confirm": confirm or password,
            },
        )

    def issue_link(self):
        self.request_reset()
        return extract_link_params(mail.outbox[-1])

    def test_request_sends_email_with_link(self):
        response = self.request_reset()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["student@example.com"])
        self.assertTrue(mail.outbox[0].body.count(settings.FRONTEND_BASE_URL))
        self.assertTrue(
            AuditLog.objects.filter(event_type=AuditEvent.PASSWORD_RESET_REQUESTED).exists()
        )

    def test_unknown_email_gets_identical_response_and_no_email(self):
        known = self.request_reset()
        unknown = self.request_reset("ghost@example.com")
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_suspended_account_gets_same_response_and_no_email(self):
        self.user.status = AccountStatus.SUSPENDED
        self.user.save()
        response = self.request_reset()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_delivery_failure_does_not_change_response(self):
        with mock.patch(
            "apps.core.email.EmailMultiAlternatives.send", side_effect=OSError("smtp down")
        ):
            response = self.request_reset()
        self.assertEqual(response.status_code, 200)

    def test_request_is_throttled(self):
        with mock.patch.dict(
            PasswordResetRequestThrottle.THROTTLE_RATES, {"password_reset_request": "2/hour"}
        ):
            codes = [self.request_reset().status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_successful_reset_changes_password(self):
        uid, token = self.issue_link()
        response = self.confirm(uid, token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.login(password=STRONG_PASSWORD).status_code, 401)  # old password dead
        self.assertEqual(self.login(password=NEW_PASSWORD).status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(event_type=AuditEvent.PASSWORD_RESET_COMPLETED).exists()
        )

    def test_token_is_single_use(self):
        uid, token = self.issue_link()
        self.assertEqual(self.confirm(uid, token).status_code, 200)
        reuse = self.confirm(uid, token, password="Yet-Another-Passw0rd-55")
        self.assertEqual(reuse.status_code, 400)
        self.assertIn("token", reuse.json()["errors"])
        self.assertEqual(self.login(password=NEW_PASSWORD).status_code, 200)

    def test_token_expires(self):
        uid, token = self.issue_link()
        later = timezone.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)
        with mock.patch.object(
            default_token_generator, "_now", return_value=later.replace(tzinfo=None)
        ):
            response = self.confirm(uid, token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.login(password=STRONG_PASSWORD).status_code, 200)

    def test_invalid_tokens_and_uids_share_one_error(self):
        uid, token = self.issue_link()
        other = make_user("other@example.com")
        other_uid = self.issue_link_for(other)
        bodies = []
        for bad_uid, bad_token in (
            (uid, "wrong-token"),
            ("!!!", token),
            ("", ""),
            (other_uid, token),  # token for a different user
            (urlsafe_base64_encode(force_bytes(uuid.uuid4())), token),  # unknown user
        ):
            response = self.confirm(bad_uid, bad_token)
            self.assertEqual(response.status_code, 400, (bad_uid, bad_token))
            bodies.append(response.json()["errors"].get("token"))
        self.assertTrue(all(bodies))
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(self.login(password=STRONG_PASSWORD).status_code, 200)

    def issue_link_for(self, user):
        mail.outbox.clear()
        self.request_reset(user.email)
        return extract_link_params(mail.outbox[-1])[0]

    def test_weak_or_mismatched_new_password_rejected_and_token_still_usable(self):
        uid, token = self.issue_link()
        self.assertEqual(self.confirm(uid, token, password="12345678901").status_code, 400)
        self.assertEqual(self.confirm(uid, token, confirm="Mismatch-Passw0rd-99").status_code, 400)
        self.assertEqual(self.confirm(uid, token).status_code, 200)

    def test_reset_revokes_existing_sessions(self):
        self.login()
        uid, token = self.issue_link()
        self.confirm(uid, token)
        self.assertGreaterEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(self.post("refresh").status_code, 401)

    def test_stored_password_is_not_plaintext(self):
        uid, token = self.issue_link()
        self.confirm(uid, token)
        self.assertNotIn(NEW_PASSWORD, User.objects.get().password)
