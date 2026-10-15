import uuid

from django.test import override_settings

from apps.accounts.models import AccountStatus, UserRole

from .helpers import ApiTestCase, make_user

ENDPOINTS = {
    UserRole.STUDENT: "/t/student/",
    UserRole.EMPLOYER: "/t/employer/",
    UserRole.INSTRUCTOR: "/t/instructor/",
    UserRole.MODERATOR: "/t/moderator/",
    UserRole.ADMINISTRATOR: "/t/admin/",
}


@override_settings(ROOT_URLCONF="apps.accounts.tests.urls")
class RolePermissionTests(ApiTestCase):
    def test_each_role_reaches_only_its_own_endpoint(self):
        for role in UserRole.values:
            self.client.credentials()
            user = make_user(f"{role}@example.com", role=role)
            self.auth_as(user)
            for endpoint_role, url in ENDPOINTS.items():
                expected = 200 if endpoint_role == role else 403
                self.assertEqual(self.client.get(url).status_code, expected, f"{role} -> {url}")

    def test_student_cannot_use_employer_endpoint(self):
        self.auth_as(make_user())
        response = self.client.get("/t/employer/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "PERMISSION_DENIED")

    def test_employer_cannot_use_administrator_endpoint(self):
        self.auth_as(make_user("hr@acme.example", role=UserRole.EMPLOYER))
        self.assertEqual(self.client.get("/t/admin/").status_code, 403)

    def test_anonymous_gets_401_not_403(self):
        self.assertEqual(self.client.get("/t/admin/").status_code, 401)

    def test_role_changes_apply_immediately(self):
        user = make_user()
        self.auth_as(user)
        self.assertEqual(self.client.get("/t/student/").status_code, 200)
        user.role = UserRole.MODERATOR
        user.save()
        self.assertEqual(self.client.get("/t/student/").status_code, 403)
        self.assertEqual(self.client.get("/t/moderator/").status_code, 200)

    def test_suspended_user_loses_access(self):
        user = make_user("mod@example.com", role=UserRole.MODERATOR)
        self.auth_as(user)
        user.status = AccountStatus.SUSPENDED
        user.save()
        self.assertEqual(self.client.get("/t/moderator/").status_code, 401)

    def test_superuser_flag_does_not_bypass_role_checks(self):
        user = make_user("root@example.com", is_superuser=True, is_staff=True)
        self.auth_as(user)
        self.assertEqual(self.client.get("/t/admin/").status_code, 403)


@override_settings(ROOT_URLCONF="apps.accounts.tests.urls")
class ObjectLevelPermissionTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.employer_a = make_user("a@acme.example", role=UserRole.EMPLOYER)
        self.employer_b = make_user("b@beta.example", role=UserRole.EMPLOYER)

    def test_owner_can_read_own_object(self):
        self.auth_as(self.employer_a)
        response = self.client.get(f"/t/company/{self.employer_a.company.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_employer_cannot_read_another_employers_object(self):
        """IDOR: knowing the other employer's UUID grants nothing."""
        self.auth_as(self.employer_a)
        response = self.client.get(f"/t/company/{self.employer_b.company.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_read_company_object(self):
        self.auth_as(make_user())
        response = self.client.get(f"/t/company/{self.employer_a.company.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_unknown_object_is_404(self):
        self.auth_as(self.employer_a)
        self.assertEqual(self.client.get(f"/t/company/{uuid.uuid4()}/").status_code, 404)
