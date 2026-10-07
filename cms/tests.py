from unittest.mock import Mock, patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ContactUs, ElectronicBillingInterest, TaxPayer


class PublicLeadEndpointsTests(APITestCase):
    @override_settings(MIDDLEWARE_ACCESS_TOKEN="")
    @patch("cms.views.EmailService.send_async")
    def test_contact_is_accepted_and_saved_when_odoo_is_not_configured(self, _send_email):
        response = self.client.post("/api/cms/contact-us/", {
            "full_name": "Ada Example",
            "email": "ada@example.com",
            "company_size": "1-20",
            "message": "Please arrange a demonstration.",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact = ContactUs.objects.get()
        self.assertEqual(contact.odoo_sync_status, "pending")

    @override_settings(
        MIDDLEWARE_ACCESS_TOKEN="middleware-test-token",
        MIDDLEWARE_BASE_URL="https://middleware.example",
        MIDDLEWARE_TENANT_ID="codestra",
    )
    @patch("helpers.middleware_client.requests.post")
    def test_billing_interest_is_sent_to_odoo(self, post):
        post.return_value = Mock(
            json=Mock(return_value={"operation_id": "op-42"}),
            raise_for_status=Mock(),
        )
        response = self.client.post("/api/cms/electronic-billing-interest/", {
            "full_name": "Grace Example",
            "email": "grace@example.com",
            "phone": "+1 555 0100",
            "uses_erp": True,
            "consent_to_contact": True,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        interest = ElectronicBillingInterest.objects.get()
        self.assertEqual(interest.odoo_sync_status, "synced")
        self.assertEqual(interest.odoo_record_id, "op-42")
        self.assertEqual(post.call_args.kwargs["timeout"], 10)

    def test_billing_interest_requires_contact_consent(self):
        response = self.client.post("/api/cms/electronic-billing-interest/", {
            "full_name": "No Consent",
            "email": "no@example.com",
            "phone": "+1 555 0101",
            "uses_erp": False,
            "consent_to_contact": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ElectronicBillingInterest.objects.count(), 0)

    @override_settings(MIDDLEWARE_ACCESS_TOKEN="")
    def test_taxpayer_registration_is_kept_when_odoo_is_offline(self):
        response = self.client.post("/api/cms/tax-payer/", {
            "tax_payer_rnc": "123456789",
            "name_of_tax_payer": "Example Company",
            "tax_payer_email": "billing@example.com",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaxPayer.objects.get().odoo_sync_status, "pending")
