import hashlib
import hmac
from unittest import mock

import requests
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import AccountStatus, SocialAccount, User
from apps.accounts.social import (
    FacebookVerifier,
    SocialAuthError,
    SocialEmailRequired,
    SocialIdentity,
)

from .helpers import ApiTestCase, make_user

FB = {"FACEBOOK_APP_ID": "1234567890", "FACEBOOK_APP_SECRET": "app-secret-xyz"}


def graph_response(payload, status=200):
    response = mock.Mock(status_code=status)
    response.json.return_value = payload
    return response


def fake_graph(debug=None, me=None):
    """Patch requests.get so /debug_token and /me return the given payloads."""
    debug = (
        {"data": {"is_valid": True, "app_id": "1234567890", "user_id": "fb-1"}}
        if debug is None
        else debug
    )
    me = (
        {"id": "fb-1", "first_name": "Fatima", "last_name": "Sesay", "email": "Fatima@Example.com"}
        if me is None
        else me
    )

    def get(url, params=None, timeout=None):
        return graph_response(debug if url.endswith("/debug_token") else me)

    return mock.patch("apps.accounts.social.requests.get", side_effect=get)


@override_settings(**FB)
class FacebookVerifierTests(ApiTestCase):
    def verifier(self):
        return FacebookVerifier("1234567890", "app-secret-xyz")

    def test_valid_token_returns_normalised_identity(self):
        with fake_graph() as get:
            identity = self.verifier().verify("user-token")
        self.assertEqual(identity.provider, "facebook")
        self.assertEqual(identity.subject, "fb-1")
        self.assertEqual(identity.email, "fatima@example.com")
        self.assertEqual((identity.first_name, identity.last_name), ("Fatima", "Sesay"))

        debug_call, me_call = get.call_args_list
        self.assertEqual(debug_call.kwargs["params"]["input_token"], "user-token")
        self.assertEqual(debug_call.kwargs["params"]["access_token"], "1234567890|app-secret-xyz")
        expected_proof = hmac.new(b"app-secret-xyz", b"user-token", hashlib.sha256).hexdigest()
        self.assertEqual(me_call.kwargs["params"]["appsecret_proof"], expected_proof)
        self.assertEqual(debug_call.kwargs["timeout"], 10)

    def test_token_issued_to_another_app_is_rejected(self):
        debug = {"data": {"is_valid": True, "app_id": "999", "user_id": "fb-1"}}
        with fake_graph(debug=debug), self.assertRaises(SocialAuthError):
            self.verifier().verify("token-for-other-app")

    def test_invalid_or_expired_token_is_rejected(self):
        debug = {"data": {"is_valid": False, "app_id": "1234567890", "user_id": "fb-1"}}
        with fake_graph(debug=debug), self.assertRaises(SocialAuthError):
            self.verifier().verify("expired")

    def test_profile_for_a_different_user_is_rejected(self):
        with fake_graph(me={"id": "someone-else", "email": "x@example.com"}):
            with self.assertRaises(SocialAuthError):
                self.verifier().verify("token")

    def test_missing_email_asks_the_user_to_share_it(self):
        with (
            fake_graph(me={"id": "fb-1", "first_name": "No"}),
            self.assertRaises(SocialEmailRequired),
        ):
            self.verifier().verify("token")

    def test_graph_errors_and_outages_are_rejected(self):
        with mock.patch("apps.accounts.social.requests.get", return_value=graph_response({}, 400)):
            with self.assertRaises(SocialAuthError):
                self.verifier().verify("token")
        with mock.patch("apps.accounts.social.requests.get", side_effect=requests.Timeout()):
            with self.assertRaises(SocialAuthError):
                self.verifier().verify("token")


@override_settings(**FB)
class FacebookLoginTests(ApiTestCase):
    url_name = "accounts:social-login"

    def facebook(self, **payload):
        body = {"credential": "user-token", **payload}
        with fake_graph():
            return self.client.post(reverse(self.url_name, args=["facebook"]), body, format="json")

    def test_providers_lists_facebook_app_id_but_never_the_secret(self):
        response = self.client.get(reverse("accounts:providers"))
        self.assertEqual(response.json()["data"]["facebook"], {"client_id": "1234567890"})
        self.assertNotIn("app-secret-xyz", response.content.decode())

    def test_new_user_needs_terms_then_gets_a_student_account(self):
        refused = self.facebook()
        self.assertEqual(refused.status_code, 400)
        self.assertEqual(refused.json()["code"], "TERMS_REQUIRED")
        self.assertEqual(User.objects.count(), 0)

        response = self.facebook(terms_accepted=True)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["user"]["role"], "student")
        self.assertEqual(data["user"]["email"], "fatima@example.com")
        self.assertEqual(data["user"]["profile"], {"first_name": "Fatima", "last_name": "Sesay"})
        self.assertIn(settings.AUTH_COOKIE_NAME, response.cookies)
        user = User.objects.get()
        self.assertFalse(user.has_usable_password())
        self.assertTrue(
            SocialAccount.objects.filter(user=user, provider="facebook", subject="fb-1").exists()
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)

    def test_returning_facebook_user_signs_in_without_terms(self):
        self.facebook(terms_accepted=True)
        response = self.facebook()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_existing_password_account_is_not_linked(self):
        make_user("fatima@example.com")
        response = self.facebook(terms_accepted=True)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "ACCOUNT_EXISTS")
        self.assertFalse(SocialAccount.objects.exists())

    def test_google_and_facebook_accounts_do_not_collide(self):
        """Same email through two providers must not silently merge accounts."""
        with (
            mock.patch(
                "apps.accounts.social.GoogleVerifier.verify",
                return_value=SocialIdentity(
                    "google", "g-1", "fatima@example.com", "Fatima", "Sesay"
                ),
            ),
            override_settings(GOOGLE_OAUTH_CLIENT_ID="g.apps.googleusercontent.com"),
        ):
            self.client.post(
                reverse(self.url_name, args=["google"]),
                {"credential": "t", "terms_accepted": True},
                format="json",
            )
        response = self.facebook(terms_accepted=True)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.objects.count(), 1)

    def test_suspended_facebook_user_is_rejected(self):
        self.facebook(terms_accepted=True)
        User.objects.update(status=AccountStatus.SUSPENDED)
        self.assertEqual(self.facebook().status_code, 401)

    def test_forged_token_is_rejected(self):
        with mock.patch(
            "apps.accounts.social.requests.get",
            return_value=graph_response({"error": {"message": "bad token"}}, 400),
        ):
            response = self.client.post(
                reverse(self.url_name, args=["facebook"]),
                {"credential": "forged", "terms_accepted": True},
                format="json",
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "SOCIAL_AUTH_FAILED")
        self.assertEqual(User.objects.count(), 0)

    def test_untrusted_origin_rejected(self):
        response = self.client.post(
            reverse(self.url_name, args=["facebook"]),
            {"credential": "t"},
            format="json",
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(FACEBOOK_APP_ID="", FACEBOOK_APP_SECRET="")
    def test_not_configured_returns_501(self):
        response = self.client.post(
            reverse(self.url_name, args=["facebook"]), {"credential": "t"}, format="json"
        )
        self.assertEqual(response.status_code, 501)
