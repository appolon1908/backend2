"""Production-startup and durable signup regressions for GH18."""
from io import StringIO
from unittest.mock import Mock, patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, override_settings
from rest_framework.test import APIClient, APITestCase

from auth_app.models import Visitor
from auth_app.tasks import sync_signup_to_middleware
from CORE.settings import MIDDLEWARE as PRODUCTION_MIDDLEWARE
from helpers.middleware_client import MiddlewareRequestError, submit_contact


class ProductionStartupTests(APITestCase):
    @override_settings(MIDDLEWARE=PRODUCTION_MIDDLEWARE)
    def test_production_middleware_boots_and_health_persists_visitor(self):
        response = Client().get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Visitor.objects.get().page, "http://testserver/healthz/")


class DeferredSignupTests(APITestCase):
    payload = {"email": "deferred@example.invalid", "password": "StrongPass123!", "first_name": "Deferred", "last_name": "User"}

    @override_settings(MIDDLEWARE_BASE_URL="https://middleware.example", MIDDLEWARE_ACCESS_TOKEN="test-token", MIDDLEWARE_TENANT_ID="codestra")
    @patch("auth_app.views.sync_signup_to_middleware.delay", side_effect=RuntimeError("sensitive broker connection details"))
    def test_signup_survives_broker_failure_without_claiming_queued(self, _delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/auth/signup/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["crm_sync"], "pending")
        user = get_user_model().objects.get(email=self.payload["email"])
        self.assertEqual(user.crm_sync_status, "pending")
        self.assertEqual(user.crm_sync_payload["email"], self.payload["email"])
        self.assertNotIn("password", user.crm_sync_payload)
        self.assertNotIn("sensitive", user.crm_sync_last_error)
        self.assertTrue(user.check_password(self.payload["password"]))

    @patch("auth_app.tasks.submit_contact")
    def test_acceptance_is_submitted_not_verified_synced(self, submit):
        submit.return_value = {"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}
        user = get_user_model().objects.create_user(email="accepted@example.invalid")
        result = sync_signup_to_middleware.apply(args=[user.pk]).get()
        user.refresh_from_db()
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(user.crm_sync_status, "submitted")
        self.assertIsNone(user.crm_synced_at)
        self.assertIsNone(user.odoo_id)

    @patch("auth_app.tasks.submit_contact")
    def test_malformed_or_failed_operations_never_become_synced(self, submit):
        for index, operation in enumerate([{}, {"operation_id": "not-a-uuid", "state": "ACCEPTED"}, {"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "FAILED"}]):
            with self.subTest(operation=operation):
                user = get_user_model().objects.create_user(email=f"bad{index}@example.invalid")
                submit.return_value = operation
                sync_signup_to_middleware.apply(args=[user.pk])
                user.refresh_from_db()
                self.assertEqual(user.crm_sync_status, "failed")
                self.assertIsNone(user.crm_synced_at)

    @override_settings(MIDDLEWARE_BASE_URL="", MIDDLEWARE_ACCESS_TOKEN="", MIDDLEWARE_TENANT_ID="")
    def test_unconfigured_recovery_preserves_pending_and_never_contacts_provider(self):
        user = get_user_model().objects.create_user(email="offline@example.invalid")
        output = StringIO()
        call_command("retry_pending_signups", limit=10, stdout=output)
        user.refresh_from_db()
        self.assertEqual(user.crm_sync_status, "pending")
        self.assertIsNone(user.crm_synced_at)

    @override_settings(MIDDLEWARE_BASE_URL="https://middleware.example", MIDDLEWARE_ACCESS_TOKEN="test-token", MIDDLEWARE_TENANT_ID="codestra")
    @patch("helpers.middleware_client.requests.post")
    def test_recovery_uses_original_payload_after_profile_changes(self, post):
        post.return_value = Mock(json=Mock(return_value={"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}), raise_for_status=Mock())
        user = get_user_model().objects.create_user(email="original@example.invalid", first_name="Original", crm_sync_payload={"email": "original@example.invalid", "first_name": "Original", "last_name": "", "phone": None, "plan_type": "FREE", "source": "codestra-signup"})
        user.email = "changed@example.invalid"
        user.save()
        output = StringIO()
        call_command("retry_pending_signups", limit=10, stdout=output)
        user.refresh_from_db()
        self.assertEqual(user.crm_sync_status, "submitted")
        self.assertEqual(post.call_args.kwargs["json"]["email"], "original@example.invalid")

    @override_settings(MIDDLEWARE_BASE_URL="https://middleware.example", MIDDLEWARE_ACCESS_TOKEN="test-token", MIDDLEWARE_TENANT_ID="codestra")
    @patch("helpers.middleware_client.requests.post")
    def test_retry_preserves_idempotency_envelope(self, post):
        post.return_value = Mock(json=Mock(return_value={"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}), raise_for_status=Mock())
        for _ in range(2):
            submit_contact({"email": "same@example.invalid"}, idempotency_key="stable-key")
        first, second = post.call_args_list
        self.assertEqual(first.kwargs["headers"], second.kwargs["headers"])
        self.assertEqual(first.kwargs["headers"]["Idempotency-Key"], "stable-key")


class RefreshFailureTests(APITestCase):
    def test_invalid_refresh_cookie_returns_401_instead_of_500(self):
        user = get_user_model().objects.create_user(email="refresh@example.invalid", password="StrongPass123!")
        client = APIClient(enforce_csrf_checks=True)
        login = client.post("/api/auth/login/", {"email": user.email, "password": "StrongPass123!"}, format="json")
        client.cookies["codestra_refresh"] = "invalid-token"
        csrf = login.cookies["csrftoken"].value
        client.cookies["csrftoken"] = csrf
        client.raise_request_exception = False
        response = client.post("/api/auth/refresh-session/", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.cookies["codestra_refresh"].value, "")

class InactiveLoginTests(APITestCase):
    def test_inactive_user_cannot_receive_authentication_cookies(self):
        user = get_user_model().objects.create_user(email="inactive@example.invalid", password="StrongPass123!")
        user.is_active = False
        user.save(update_fields=["is_active"])
        response = self.client.post("/api/auth/login/", {"email": user.email, "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("codestra_access", response.cookies)
        self.assertNotIn("codestra_refresh", response.cookies)

class RecoverySelectionTests(APITestCase):
    @override_settings(MIDDLEWARE_BASE_URL="https://middleware.example", MIDDLEWARE_ACCESS_TOKEN="test-token", MIDDLEWARE_TENANT_ID="codestra")
    @patch("helpers.middleware_client.requests.post")
    def test_recovery_queues_only_unbound_accounts_with_a_durable_signup_intent(self, post):
        post.return_value = Mock(json=Mock(return_value={"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}), raise_for_status=Mock())
        intended = get_user_model().objects.create_user(email="intent@example.invalid", crm_sync_payload={"email": "intent@example.invalid", "source": "codestra-signup"})
        legacy = get_user_model().objects.create_user(email="legacyadmin@example.invalid", is_staff=True)
        linked = get_user_model().objects.create_user(email="bound@example.invalid", odoo_id=123, crm_sync_payload={"email": "bound@example.invalid", "source": "codestra-signup"})
        call_command("retry_pending_signups", limit=10, stdout=StringIO())
        intended.refresh_from_db()
        legacy.refresh_from_db()
        linked.refresh_from_db()
        self.assertEqual(intended.crm_sync_status, "submitted")
        self.assertEqual(legacy.crm_sync_status, "pending")
        self.assertEqual(legacy.crm_sync_operation_id, "")
        self.assertEqual(linked.crm_sync_operation_id, "")
        self.assertEqual(linked.odoo_id, 123)


class UnavailableCalendarTests(APITestCase):
    @override_settings(ODOO_API_TOKEN="", ODOO_BASE_URL="")
    def test_authenticated_calendar_is_503_when_integration_is_absent(self):
        user = get_user_model().objects.create_user(email="calendar@example.invalid")
        self.client.force_authenticate(user)
        for url in ["/api/calendar/", "/api/calendar/123/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 503)

class LogoutExpiryTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="logout-expiry@example.invalid", password="StrongPass123!")
        self.browser = APIClient(enforce_csrf_checks=True)
        login = self.browser.post("/api/auth/login/", {"email": self.user.email, "password": "StrongPass123!"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.csrf = login.cookies["csrftoken"].value
        self.refresh = login.cookies["codestra_refresh"].value

    def test_logout_after_access_expiry_revokes_refresh_and_clears_cookies(self):
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=-1))
        self.browser.cookies["codestra_access"] = str(token)
        response = self.browser.post("/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 205)
        for name in ["codestra_access", "codestra_refresh"]:
            self.assertEqual(response.cookies[name].value, "")
            self.assertEqual(response.cookies[name]["max-age"], 0)
        self.browser.cookies["codestra_refresh"] = self.refresh
        response = self.browser.post("/api/auth/refresh-session/", {}, format="json", HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.browser.get("/api/auth/session/").status_code, 401)

    def test_logout_is_idempotent_without_access_or_valid_refresh(self):
        del self.browser.cookies["codestra_access"]
        self.browser.cookies["codestra_refresh"] = "malformed-refresh"
        for _ in range(2):
            response = self.browser.post("/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=self.csrf)
            self.assertEqual(response.status_code, 205)
            for name in ["codestra_access", "codestra_refresh"]:
                self.assertEqual(response.cookies[name].value, "")

    def test_logout_rejects_missing_csrf_without_revoking_refresh(self):
        self.browser.cookies["codestra_access"] = "malformed-access"
        response = self.browser.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("codestra_refresh", response.cookies)
        response = self.browser.post("/api/auth/refresh-session/", {}, format="json", HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 200)
