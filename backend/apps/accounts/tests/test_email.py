from unittest import mock

from django.core import mail
from django.test import override_settings

from apps.core.email import BrevoEmailSender, EmailDeliveryError, deliver_email

from .helpers import ApiTestCase, company_payload, make_user, student_payload

BREVO = {
    "BREVO_API_KEY": "xkeysib-test",
    "EMAIL_FROM_ADDRESS": "hello@edunext.example",
    "EMAIL_FROM_NAME": "EduNext SL",
}


def html_of(message):
    return next(content for content, mimetype in message.alternatives if mimetype == "text/html")


@override_settings(**BREVO)
class BrevoSenderTests(ApiTestCase):
    def test_posts_branded_payload_with_api_key_header(self):
        response = mock.Mock(status_code=201)
        with mock.patch("apps.core.email.requests.post", return_value=response) as post:
            BrevoEmailSender().send(to="a@b.co", subject="Hi", body="text", html="<p>x</p>")
        kwargs = post.call_args.kwargs
        self.assertEqual(post.call_args.args[0], "https://api.brevo.com/v3/smtp/email")
        self.assertEqual(kwargs["headers"]["api-key"], "xkeysib-test")
        self.assertEqual(
            kwargs["json"]["sender"], {"name": "EduNext SL", "email": "hello@edunext.example"}
        )
        self.assertEqual(kwargs["json"]["to"], [{"email": "a@b.co"}])
        self.assertEqual(kwargs["json"]["htmlContent"], "<p>x</p>")
        self.assertEqual(kwargs["timeout"], 10)

    def test_provider_error_does_not_leak_recipient_or_key(self):
        response = mock.Mock(status_code=401)
        response.json.return_value = {"code": "unauthorized", "message": "a@b.co key invalid"}
        with mock.patch("apps.core.email.requests.post", return_value=response):
            with self.assertRaises(EmailDeliveryError) as ctx:
                BrevoEmailSender().send(to="a@b.co", subject="Hi", body="t")
        self.assertIn("401", str(ctx.exception))
        self.assertNotIn("a@b.co", str(ctx.exception))
        self.assertNotIn("xkeysib", str(ctx.exception))

    def test_network_failure_becomes_delivery_error(self):
        import requests

        with mock.patch("apps.core.email.requests.post", side_effect=requests.Timeout("slow")):
            with self.assertRaises(EmailDeliveryError):
                BrevoEmailSender().send(to="a@b.co", subject="Hi", body="t")


class DeliverEmailTests(ApiTestCase):
    def test_failures_are_swallowed_and_logged(self):
        with mock.patch("apps.core.email.get_email_sender", side_effect=RuntimeError("boom")):
            with self.assertLogs("apps.core.email", level="ERROR"):
                deliver_email(to="a@b.co", subject="s", body="b")  # must not raise

    @override_settings(EMAIL_ASYNC=True)
    def test_async_mode_uses_a_background_thread(self):
        with mock.patch("apps.core.email.threading.Thread") as thread:
            deliver_email(to="a@b.co", subject="s", body="b")
        thread.return_value.start.assert_called_once()


@override_settings(EMAIL_LOGO_URL="https://cdn.example/logo.jpg")
class BrandedEmailTests(ApiTestCase):
    def test_welcome_email_for_student(self):
        self.post("register-student", student_payload(first_name="Aminata"))
        message = mail.outbox[0]
        self.assertEqual(message.to, ["aminata@example.com"])
        self.assertIn("Welcome to EduNext SL", message.subject)
        self.assertIn("Aminata", message.body)
        html = html_of(message)
        self.assertIn("https://cdn.example/logo.jpg", html)
        self.assertIn("/login", html)
        self.assertNotIn("pending verification", html)

    def test_welcome_email_for_company_mentions_verification(self):
        self.post("register-company", company_payload())
        message = mail.outbox[0]
        self.assertIn("Salone Tech Ltd", message.body)
        self.assertIn("pending verification", html_of(message))

    def test_user_supplied_names_are_escaped_in_html(self):
        self.post("register-student", student_payload(first_name="<script>alert(1)</script>"))
        html = html_of(mail.outbox[0])
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_registration_survives_email_failure(self):
        with mock.patch("apps.core.email.EmailMultiAlternatives.send", side_effect=OSError("down")):
            response = self.post("register-student", student_payload())
        self.assertEqual(response.status_code, 201)

    def test_password_reset_email_is_branded_with_link(self):
        make_user()
        self.post("password-reset-request", {"email": "student@example.com"})
        message = mail.outbox[0]
        html = html_of(message)
        self.assertIn("Choose a new password", html)
        self.assertIn("reset-password?uid=", html)
        self.assertIn("expires in 60 minutes", html)
        self.assertIn("reset-password?uid=", message.body)
