from unittest import mock

from django.test import override_settings

from apps.accounts.models import AccountStatus, LegalAcceptance, StudentProfile, User, UserRole
from apps.companies.models import Company, VerificationStatus
from apps.core.models import AuditEvent, AuditLog

from .helpers import ApiTestCase, company_payload, make_user, student_payload


class StudentRegistrationTests(ApiTestCase):
    def test_valid_registration(self):
        response = self.post("register-student", student_payload())
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["success"])
        user_data = body["data"]["user"]
        self.assertEqual(user_data["role"], "student")
        self.assertEqual(user_data["status"], "active")
        self.assertEqual(user_data["profile"], {"first_name": "Aminata", "last_name": "Kamara"})
        self.assertNotIn("password", str(body))

        user = User.objects.get(email="aminata@example.com")
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertTrue(user.check_password("Tr1cky-Horse-Battery-92"))
        self.assertNotEqual(user.password, "Tr1cky-Horse-Battery-92")
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    @override_settings(
        PASSWORD_HASHERS=[
            "django.contrib.auth.hashers.Argon2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        ]
    )
    def test_password_is_hashed_with_argon2(self):
        self.post("register-student", student_payload())
        self.assertTrue(User.objects.get().password.startswith("argon2$"))

    def test_email_is_normalized_and_duplicates_are_case_insensitive(self):
        self.post("register-student", student_payload(email="  Mixed.Case@Example.COM "))
        self.assertTrue(User.objects.filter(email="mixed.case@example.com").exists())

        response = self.post("register-student", student_payload(email="MIXED.case@example.com"))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "EMAIL_ALREADY_REGISTERED")
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_email(self):
        response = self.post("register-student", student_payload(email="not-an-email"))
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["code"], "VALIDATION_ERROR")
        self.assertFalse(body["success"])
        self.assertIn("email", body["errors"])

    def test_weak_password(self):
        for weak in ("short1!", "password1234", "1234567890123"):
            response = self.post(
                "register-student",
                student_payload(email=f"{weak}@example.com", password=weak, password_confirm=weak),
            )
            self.assertEqual(response.status_code, 400, weak)
            self.assertIn("password", response.json()["errors"])
        self.assertEqual(User.objects.count(), 0)

    def test_password_similar_to_email_is_rejected(self):
        response = self.post(
            "register-student",
            student_payload(
                email="aminatakamara@example.com",
                password="aminatakamara1",
                password_confirm="aminatakamara1",
            ),
        )
        self.assertEqual(response.status_code, 400)

    def test_password_mismatch(self):
        response = self.post(
            "register-student", student_payload(password_confirm="Different-Pass-123")
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.json()["errors"])

    def test_terms_must_be_accepted(self):
        for value in (False, None):
            response = self.post("register-student", student_payload(terms_accepted=value))
            self.assertEqual(response.status_code, 400)
            self.assertIn("terms_accepted", response.json()["errors"])
        response = self.post(
            "register-student",
            {k: v for k, v in student_payload().items() if k != "terms_accepted"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    @override_settings(
        LEGAL_TERMS_VERSION="t-1",
        LEGAL_USER_AGREEMENT_VERSION="u-2",
        LEGAL_PRIVACY_POLICY_VERSION="p-3",
    )
    def test_legal_acceptance_is_recorded(self):
        self.post("register-student", student_payload())
        acceptance = LegalAcceptance.objects.get()
        self.assertEqual(
            (
                acceptance.terms_version,
                acceptance.user_agreement_version,
                acceptance.privacy_policy_version,
            ),
            ("t-1", "u-2", "p-3"),
        )

    def test_client_cannot_choose_role_or_status(self):
        self.post(
            "register-student",
            student_payload(
                role="administrator", status="pending", is_staff=True, is_superuser=True
            ),
        )
        user = User.objects.get()
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertEqual(user.status, AccountStatus.ACTIVE)
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_duplicate_email_conflict_from_race(self):
        """If the pre-check passes but the DB constraint fires, the API still answers 409."""
        make_user("aminata@example.com")
        with mock.patch(
            "apps.accounts.serializers._RegistrationSerializer.validate_email_unique",
            side_effect=lambda email: email,
        ):
            response = self.post("register-student", student_payload())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "EMAIL_ALREADY_REGISTERED")
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rolls_back_when_a_step_fails(self):
        with mock.patch(
            "apps.accounts.services._record_legal_acceptance", side_effect=RuntimeError("boom")
        ):
            self.client.raise_request_exception = False
            response = self.post("register-student", student_payload())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["code"], "INTERNAL_ERROR")
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(StudentProfile.objects.count(), 0)

    def test_registration_is_audited_without_secrets(self):
        self.post("register-student", student_payload())
        event = AuditLog.objects.get(event_type=AuditEvent.REGISTRATION)
        self.assertEqual(event.actor.email, "aminata@example.com")
        self.assertNotIn("Tr1cky", str(event.metadata))


class CompanyRegistrationTests(ApiTestCase):
    def test_valid_registration(self):
        response = self.post("register-company", company_payload())
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]["user"]
        self.assertEqual(data["role"], "employer")
        self.assertEqual(data["profile"]["name"], "Salone Tech Ltd")
        self.assertEqual(data["profile"]["verification_status"], VerificationStatus.PENDING)

        company = Company.objects.get()
        self.assertEqual(company.owner.email, "hr@salonetech.example")
        self.assertEqual(company.work_email, "hr@salonetech.example")
        self.assertEqual(LegalAcceptance.objects.count(), 1)

    def test_duplicate_work_email(self):
        make_user("hr@salonetech.example")
        response = self.post("register-company", company_payload())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "EMAIL_ALREADY_REGISTERED")

    def test_requires_terms_and_matching_passwords(self):
        self.assertEqual(
            self.post("register-company", company_payload(terms_accepted=False)).status_code, 400
        )
        self.assertEqual(
            self.post(
                "register-company", company_payload(password_confirm="nope-nope-nope")
            ).status_code,
            400,
        )
        self.assertEqual(Company.objects.count(), 0)

    def test_missing_fields(self):
        response = self.post("register-company", {})
        self.assertEqual(response.status_code, 400)
        for field in (
            "company_name",
            "contact_full_name",
            "work_email",
            "password",
            "terms_accepted",
        ):
            self.assertIn(field, response.json()["errors"])
