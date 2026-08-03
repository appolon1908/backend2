from unittest.mock import Mock, patch
from payment_app.models import StripeWebhookEvent, WebhookSubscription
from payment_app.views import StripeService

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class PaymentSecurityTests(APITestCase):
    def test_webhook_secret_is_enveloped_and_never_plaintext(self):
        user = get_user_model().objects.create_user(email="envelope@example.invalid", password="safe-password")
        self.client.force_authenticate(user=user)
        created = self.client.post("/api/payment/subscriptions/", {"name": "Envelope", "url": "https://receiver.example.invalid/hooks", "events": ["test"]}, format="json")
        self.assertEqual(created.status_code, 201)
        row = WebhookSubscription.objects.get(pk=created.data["id"])
        self.assertNotIn("secret", {field.name for field in WebhookSubscription._meta.fields})
        self.assertNotEqual(row.secret_ciphertext, created.data["secret"])
        self.assertEqual(row.current_secret(), created.data["secret"])

    def test_admin_rotation_keeps_bounded_previous_overlap(self):
        user = get_user_model().objects.create_user(email="rotate@example.invalid", password="safe-password", is_staff=True)
        self.client.force_authenticate(user=user)
        created = self.client.post("/api/payment/subscriptions/", {"name": "Rotate", "url": "https://receiver.example.invalid/hooks", "events": ["test"]}, format="json")
        row = WebhookSubscription.objects.get(pk=created.data["id"])
        old = created.data["secret"]
        rotated = self.client.post(f"/api/payment/subscriptions/{row.pk}/rotate-secret/", {}, format="json")
        row.refresh_from_db()
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(old, rotated.data["secret"])
        self.assertEqual(row.current_secret(), rotated.data["secret"])
        self.assertEqual(row.previous_secret(), old)
    def test_authenticated_subscription_crud_and_secret_delivery(self):
        user = get_user_model().objects.create_user(email="hooks@example.invalid", password="safe-password")
        self.client.force_authenticate(user=user)
        created = self.client.post("/api/payment/subscriptions/", {"name": "Staging", "url": "https://receiver.example.invalid/hooks", "events": ["test"]}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data["secret"])
        subscription_id = created.data["id"]
        self.assertEqual(self.client.patch(f"/api/payment/subscriptions/{subscription_id}/", {"enabled": False}, format="json").status_code, 200)
        self.assertEqual(self.client.get("/api/payment/subscriptions/").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/payment/subscriptions/{subscription_id}/").status_code, 204)

    @patch("payment_app.webhook_api._valid_signature", return_value=True)
    def test_staging_receiver_accepts_verified_event(self, valid_signature):
        with self.settings(WEBHOOK_STAGING_MODE=True, WEBHOOK_STAGING_SECRET="stage-secret"):
            response = self.client.post("/api/payment/staging-receiver/", {"event": "test"}, format="json", HTTP_X_CODEStra_SIGNATURE="valid", HTTP_X_CODEStra_EVENT_ID="evt-stage")
        self.assertEqual(response.status_code, 202)
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
