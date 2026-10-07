from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase
from auth_app.tasks import sync_signup_to_middleware


class UserAuthorizationTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@example.invalid", password="test-password", first_name="Owner", last_name="User"
        )
        self.attacker = get_user_model().objects.create_user(
            email="attacker@example.invalid", password="test-password", first_name="Attack", last_name="User"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.attacker)

    def test_user_cannot_retrieve_another_user(self):
        response = self.client.get(f"/api/auth/users/{self.owner.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_user_list_only_contains_authenticated_user(self):
        response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.attacker.pk)

    def test_non_admin_cannot_list_visitors(self):
        response = self.client.get("/api/auth/visitors/")
        self.assertEqual(response.status_code, 403)




class SignupMiddlewareBoundaryTests(APITestCase):
    @patch("auth_app.views.sync_signup_to_middleware.delay")
    def test_signup_commits_locally_and_queues_crm_sync(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/auth/signup/",
                {
                    "email": "new@example.invalid",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "User",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["crm_sync"], "queued")
        user = get_user_model().objects.get(email="new@example.invalid")
        self.assertEqual(user.crm_sync_status, "pending")
        delay.assert_called_once_with(user.pk)


class BrowserCookieSessionTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            email="cookie@example.invalid",
            password="StrongPass123!",
            first_name="Cookie",
            last_name="User",
        )

    def login(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "StrongPass123!"},
            format="json",
        )

    def test_login_sets_http_only_tokens_and_does_not_return_tokens(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("token", response.data)
        self.assertTrue(response.cookies["codestra_access"]["httponly"])
        self.assertTrue(response.cookies["codestra_refresh"]["httponly"])
        self.assertEqual(response.cookies["codestra_access"]["samesite"], "Strict")

    def test_cookie_session_authenticates_get(self):
        login = self.login()
        self.client.cookies["codestra_access"] = login.cookies["codestra_access"].value
        session = self.client.get("/api/auth/session/")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.data["user"]["email"], self.user.email)

    def test_login_response_never_exposes_access_token(self):
        login = self.login()
        self.assertIn("codestra_access", login.cookies)
        self.assertNotIn("access", login.data)

    def test_cookie_authenticated_post_requires_csrf(self):
        login = self.login()
        self.client.cookies["codestra_access"] = login.cookies["codestra_access"].value
        self.client.cookies["codestra_refresh"] = login.cookies["codestra_refresh"].value
        response = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_cookie_authenticated_logout_with_csrf_clears_session(self):
        login = self.login()
        self.client.cookies["codestra_access"] = login.cookies["codestra_access"].value
        self.client.cookies["codestra_refresh"] = login.cookies["codestra_refresh"].value
        csrf = login.cookies["csrftoken"].value
        self.client.cookies["csrftoken"] = csrf
        response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 205)
        self.assertEqual(response.cookies["codestra_access"].value, "")
        self.assertEqual(response.cookies["codestra_refresh"].value, "")


class SignupSyncTaskTests(APITestCase):
    @override_settings(
        MIDDLEWARE_BASE_URL="https://middleware.example",
        MIDDLEWARE_ACCESS_TOKEN="test-token",
        MIDDLEWARE_TENANT_ID="codestra",
    )
    @patch("auth_app.tasks.submit_contact")
    def test_task_records_middleware_operation(self, submit_contact):
        submit_contact.return_value = {
            "operation_id": "op-signup-1",
            "state": "accepted",
        }
        user = get_user_model().objects.create_user(
            email="queued@example.invalid",
            password="StrongPass123!",
            first_name="Queued",
            last_name="User",
        )
        result = sync_signup_to_middleware.apply(args=[user.pk]).get()
        user.refresh_from_db()
        self.assertEqual(result["status"], "synced")
        self.assertEqual(user.crm_sync_status, "synced")
        self.assertEqual(user.crm_sync_operation_id, "op-signup-1")
        submit_contact.assert_called_once()
