from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


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
