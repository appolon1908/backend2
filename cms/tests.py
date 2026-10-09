from unittest.mock import Mock, patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ContactUs, ElectronicBillingInterest, TaxPayer


class PublicLeadEndpointsTests(APITestCase):
    @override_settings(ODOO_API_TOKEN="")
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
        ODOO_LEAD_SYNC_ENABLED=True,
        ODOO_LEAD_SYNC_TOKEN="write-only-test-token",
        ODOO_LEAD_SYNC_BASE_URL="https://odoo.example",
    )
    @patch("cms.odoo.requests.post")
    def test_billing_interest_is_sent_to_odoo(self, post):
        post.return_value = Mock(
            json=Mock(return_value={"lead_id": 42}),
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
        self.assertEqual(interest.odoo_record_id, "42")
        self.assertEqual(post.call_args.kwargs["timeout"], 10)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer write-only-test-token")

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

    @override_settings(ODOO_API_TOKEN="")
    def test_taxpayer_registration_is_kept_when_odoo_is_offline(self):
        response = self.client.post("/api/cms/tax-payer/", {
            "tax_payer_rnc": "123456789",
            "name_of_tax_payer": "Example Company",
            "tax_payer_email": "billing@example.com",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaxPayer.objects.get().odoo_sync_status, "pending")


class OdooDashboardReadProxyTests(APITestCase):
    """No public CRM data, no arbitrary upstream proxy and clear outages."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        cls.staff = User.objects.create_user(
            email="crm-staff@example.test", password="test-pass-123",
            is_staff=True,
        )
        cls.ordinary = User.objects.create_user(
            email="crm-user@example.test", password="test-pass-123",
            is_staff=False,
        )
        cls.unbound_staff = User.objects.create_user(
            email="crm-unbound-staff@example.test", password="test-pass-123",
            is_staff=True,
        )
        from django.contrib.auth.models import Group
        crm_group, _ = Group.objects.get_or_create(name="Codestra Call Center Super User")
        cls.staff.groups.add(crm_group)

    def test_unauthenticated_and_ordinary_users_cannot_read_crm(self):
        for url in (
            "/api/cms/odoo-crm/overview/",
            "/api/cms/odoo-crm/campaigns/",
            "/api/cms/odoo-crm/leads/",
        ):
            self.assertIn(self.client.get(url).status_code, (401, 403))
            self.client.force_authenticate(user=self.ordinary)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.force_authenticate(user=self.unbound_staff)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.force_authenticate(user=None)

    @override_settings(ODOO_API_TOKEN="", ODOO_BASE_URL="https://crm.example.test")
    def test_no_key_returns_explicit_unavailable_not_sample_data(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/cms/odoo-crm/overview/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "odoo_not_configured")

    @override_settings(ODOO_API_TOKEN="test-odoo-api-key", ODOO_BASE_URL="https://crm.example.test")
    @patch("cms.odoo_dashboard.requests.get")
    def test_authenticated_staff_proxy_passes_bearer_and_query_bounds(self, get):
        get.return_value = Mock(
            status_code=200,
            headers={"Content-Type": "application/json"},
            json=Mock(return_value={
                "schema_version": 1, "role": "superuser",
                "total": 1, "page": 1, "limit": 10,
                "campaigns": [{"id": 5, "code": "CAMP-A", "name": "Campaign A"}],
            }),
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/cms/odoo-crm/campaigns/?page=1&limit=10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertIn("no-store", response["Cache-Control"])
        _, kwargs = get.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-odoo-api-key")
        self.assertEqual(kwargs["timeout"], (3, 10))
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["params"], {"page": 1, "limit": 10})

    @override_settings(ODOO_API_TOKEN="test-odoo-api-key", ODOO_BASE_URL="https://crm.example.test")
    @patch("cms.odoo_dashboard.requests.get")
    def test_untrusted_params_or_bad_upstream_cannot_leak_crm(self, get):
        self.client.force_authenticate(user=self.staff)
        self.assertEqual(self.client.get(
            "/api/cms/odoo-crm/leads/?limit=1000"
        ).status_code, 400)
        get.assert_not_called()
        get.return_value = Mock(
            status_code=200,
            headers={"Content-Type": "text/html"},
            json=Mock(return_value={"schema_version": 1}),
        )
        response = self.client.get("/api/cms/odoo-crm/overview/")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["error"], "odoo_invalid_response")


    @override_settings(ODOO_API_TOKEN="restricted-example-key", ODOO_BASE_URL="https://crm.example.test")
    @patch("cms.odoo_dashboard.requests.get")
    def test_incorrect_odoo_account_role_fails_closed(self, get):
        get.return_value = Mock(
            status_code=200, headers={"Content-Type":"application/json"},
            json=Mock(return_value={"schema_version":1,"role":"agent","campaigns":[]}),
        )
        self.client.force_authenticate(user=self.staff)
        response=self.client.get("/api/cms/odoo-crm/campaigns/")
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.data["error"],"odoo_service_role_mismatch")


    @override_settings(
        ODOO_API_TOKEN="readonly-dashboard-token",
        ODOO_BASE_URL="https://crm.example",
        ODOO_LEAD_SYNC_ENABLED=False,
        ODOO_LEAD_SYNC_TOKEN="",
    )
    @patch("cms.odoo.requests.post")
    def test_readonly_crm_api_key_never_activates_public_lead_delivery(self, post):
        response = self.client.post("/api/cms/electronic-billing-interest/", {
            "full_name": "No external effects",
            "email": "disabled@example.invalid",
            "phone": "+1 555 0110",
            "uses_erp": True,
            "consent_to_contact": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        interest = ElectronicBillingInterest.objects.get()
        self.assertEqual(interest.odoo_sync_status, "pending")
        post.assert_not_called()

    @override_settings(
        ODOO_LEAD_SYNC_ENABLED=True,
        ODOO_LEAD_SYNC_TOKEN="write-only-test-token",
        ODOO_LEAD_SYNC_BASE_URL="http://odoo.example",
    )
    @patch("cms.odoo.requests.post")
    def test_effectful_lead_delivery_refuses_plain_http(self, post):
        response = self.client.post("/api/cms/electronic-billing-interest/", {
            "full_name": "Blocked insecure transport",
            "email": "insecure@example.invalid",
            "phone": "+1 555 0111",
            "uses_erp": True,
            "consent_to_contact": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectronicBillingInterest.objects.get().odoo_sync_status, "pending")
        post.assert_not_called()
