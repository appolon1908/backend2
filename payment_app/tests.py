from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class PaymentSecurityTests(APITestCase):
    def test_payment_creation_requires_authentication(self):
        response = self.client.post(
            "/api/payment/stipe-payment/",
            {"email": "payer@example.invalid", "name": "Payer", "amount": "10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    @patch("payment_app.webhook.stripe.Webhook.construct_event", side_effect=ValueError)
    def test_invalid_webhook_payload_returns_400(self, construct_event):
        response = self.client.post(
            "/api/payment/stripe-webhook/",
            b"not-json",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )
        self.assertEqual(response.status_code, 400)
