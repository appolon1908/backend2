from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase


class PaymentSecurityTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="payer@example.invalid",
            password="test-password",
            first_name="Pay",
            last_name="Er",
        )
        self.client = APIClient()

    def test_payment_creation_requires_authentication(self):
        response = self.client.post(
            "/api/payment/stipe-payment/",
            {"email": "payer@example.invalid", "name": "Payer", "product_code": "standard"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_client_supplied_amount_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/payment/stipe-payment/",
            {
                "email": "payer@example.invalid",
                "name": "Payer",
                "product_code": "standard",
                "amount": "1.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.data)

    @override_settings(PAYMENT_PRICE_CATALOG={"standard": "123.45"})
    @patch("payment_app.service.stripe.PaymentIntent.create")
    @patch("payment_app.service.stripe.Customer.create")
    def test_server_catalog_controls_payment_amount(self, customer_create, payment_create):
        self.client.force_authenticate(self.user)
        customer_create.return_value = {"id": "cus_test"}
        payment_create.return_value = {
            "id": "pi_test",
            "client_secret": "secret_test",
            "status": "requires_payment_method",
            "currency": "usd",
            "payment_method": None,
            "payment_method_configuration_details": None,
        }

        response = self.client.post(
            "/api/payment/stipe-payment/",
            {
                "email": "payer@example.invalid",
                "name": "Payer",
                "product_code": "standard",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payment_create.call_args.kwargs["amount"], 12345)
        self.assertEqual(
            payment_create.call_args.kwargs["metadata"]["product_code"],
            "standard",
        )

    @patch("payment_app.webhook.stripe.Webhook.construct_event", side_effect=ValueError)
    def test_invalid_webhook_payload_returns_400(self, construct_event):
        response = self.client.post(
            "/api/payment/stripe-webhook/",
            b"not-json",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )
        self.assertEqual(response.status_code, 400)
