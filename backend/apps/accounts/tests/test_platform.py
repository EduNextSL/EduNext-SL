from django.urls import reverse

from apps.accounts.models import AccountStatus, User, UserRole
from apps.core.models import AuditEvent, AuditLog

from .helpers import ApiTestCase, make_user


class DocsAndErrorShapeTests(ApiTestCase):
    def test_openapi_schema_documents_every_auth_endpoint(self):
        response = self.client.get(
            "/api/v1/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json"
        )
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        for path in (
            "/api/v1/auth/register/student/",
            "/api/v1/auth/register/company/",
            "/api/v1/auth/login/",
            "/api/v1/auth/refresh/",
            "/api/v1/auth/logout/",
            "/api/v1/auth/me/",
            "/api/v1/auth/password-reset/request/",
            "/api/v1/auth/password-reset/confirm/",
        ):
            self.assertIn(path, paths)

    def test_unknown_api_path_returns_json_404(self):
        response = self.client.get("/api/v1/auth/nope/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["code"], "NOT_FOUND")

    def test_method_not_allowed_and_bad_json_use_standard_shape(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["code"], "METHOD_NOT_ALLOWED")
        bad = self.client.post(
            reverse("accounts:login"), "{not json", content_type="application/json"
        )
        self.assertEqual(bad.status_code, 400)
        self.assertFalse(bad.json()["success"])


class AdminTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser("root@example.com", "Sup3r-Secret-Passw0rd")
        self.client.force_login(self.admin)

    def test_superuser_is_administrator(self):
        self.assertEqual(self.admin.role, UserRole.ADMINISTRATOR)

    def test_admin_pages_load(self):
        for name in (
            "accounts_user",
            "accounts_studentprofile",
            "companies_company",
            "core_auditlog",
        ):
            self.assertEqual(
                self.client.get(reverse(f"admin:{name}_changelist")).status_code, 200, name
            )

    def test_status_change_in_admin_is_audited(self):
        user = make_user()
        url = reverse("admin:accounts_user_change", args=[user.pk])
        data = {
            "email": user.email,
            "password": user.password,
            "role": user.role,
            "status": AccountStatus.SUSPENDED,
            "is_active": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        event = AuditLog.objects.get(event_type=AuditEvent.ACCOUNT_STATUS_CHANGED)
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(event.metadata["to"], "suspended")

    def test_audit_log_is_read_only_in_admin(self):
        self.assertEqual(self.client.get(reverse("admin:core_auditlog_add")).status_code, 403)
