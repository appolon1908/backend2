from unittest.mock import Mock, patch
from payment_app.models import StripeWebhookEvent
from payment_app.views import StripeService

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class PaymentSecurityTests(APITestCase):
    @patch.object(StripeService, "create_payment_intent", return_value={"client_secret": "cs_test"})
    def test_authenticated_payment_contract_uses_canonical_route(self, create_intent):
        user = get_user_model().objects.create_user(email="auth@example.invalid", password="safe-password")
        self.client.force_authenticate(user=user)
        response = self.client.post(
            "/api/payment/stripe-payment/",
            {"email": "payer@example.invalid", "name": "Payer", "amount": "10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["client_secret"], "cs_test")
        create_intent.assert_called_once()

    def test_payment_creation_requires_authentication(self):
        response = self.client.post(
            "/api/payment/stripe-payment/",
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

    @patch("payment_app.webhook.stripe.Webhook.construct_event")
    def test_signed_webhook_is_processed_once(self, construct_event):
        construct_event.return_value = {
            "id": "evt_contract_1", "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_missing", "status": "failed"}},
        }
        with self.settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            first = self.client.post("/api/payment/stripe-webhook/", b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="valid")
            second = self.client.post("/api/payment/stripe-webhook/", b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="valid")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        receipt = StripeWebhookEvent.objects.get(event_id="evt_contract_1")
        self.assertEqual(receipt.status, "processed")
        self.assertEqual(receipt.attempts, 1)

    @patch("payment_app.webhook.stripe.Webhook.construct_event")
    @patch("payment_app.webhook.Transaction.objects.filter")
    def test_processing_failure_returns_5xx_then_allows_retry(self, filter_transactions, construct_event):
        construct_event.return_value = {
            "id": "evt_contract_retry", "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_retry", "status": "failed"}},
        }
        filter_transactions.side_effect = [RuntimeError("temporary database failure"), Mock(first=lambda: None)]
        with self.settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            first = self.client.post("/api/payment/stripe-webhook/", b"retry", content_type="application/json", HTTP_STRIPE_SIGNATURE="valid")
            second = self.client.post("/api/payment/stripe-webhook/", b"retry", content_type="application/json", HTTP_STRIPE_SIGNATURE="valid")
        self.assertEqual(first.status_code, 500)
        self.assertEqual(second.status_code, 200)
        receipt = StripeWebhookEvent.objects.get(event_id="evt_contract_retry")
        self.assertEqual(receipt.status, "processed")
        self.assertEqual(receipt.attempts, 2)
