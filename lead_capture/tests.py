from unittest.mock import Mock, patch
from unittest import mock

import requests
from django.test import override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import AnalyticsEvent, LeadSubmission
from .tasks import deliver_lead
from .views import _client_ip


def lead_payload(**overrides):
    payload = {
        "full_name": "Ada Example",
        "business_name": "Example Logistics",
        "work_email": "ada@example.com",
        "phone_number": "+1 (555) 010-0200",
        "country": "United States",
        "preferred_language": "English",
        "industry": "Transportation and logistics",
        "employee_count": "11-50",
        "monthly_call_volume": "1000-5000",
        "product_interest": "AI Receptionist",
        "preferred_demo_date": "2026-08-10",
        "preferred_demo_time": "14:30",
        "message": "We need after-hours lead capture.",
        "consent": True,
        "attribution": {"utm_source": "test"},
        "landing_page_url": "https://codestra.co/ai-receptionist",
        "referrer": "https://example.com/",
        "cta_clicked": "Book a Live Demo",
        "anonymous_session_id": "session-test-123",
        "honeypot": "",
    }
    payload.update(overrides)
    return payload


TEST_RUNTIME = {
    "CACHES": {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    "CELERY_TASK_ALWAYS_EAGER": True,
    "CELERY_TASK_EAGER_PROPAGATES": True,
}


@override_settings(LEAD_DELIVERY_MODE="mock", **TEST_RUNTIME)
class LeadSubmissionTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_canonical_conversion_endpoints_accept_the_same_validated_contract(self):
        for index, endpoint in enumerate(("demo-requests", "pricing-requests", "contact-requests")):
            payload = lead_payload(work_email=f"{endpoint}@example.com", phone_number=f"+155501002{index + 1}")
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(f"/api/v1/{endpoint}", payload, format="json", HTTP_IDEMPOTENCY_KEY=f"canonical-{endpoint}")
            self.assertEqual(response.status_code, 202)

    def test_mock_submission_normalizes_phone_and_delivers(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/v1/leads", lead_payload(), format="json", HTTP_IDEMPOTENCY_KEY="request-one")
        self.assertEqual(response.status_code, 202)
        lead = LeadSubmission.objects.get()
        lead.refresh_from_db()
        self.assertEqual(lead.phone_number, "+15550100200")
        self.assertEqual(lead.delivery_status, "delivered")
        self.assertTrue(lead.delivery_reference.startswith("mock-"))
        self.assertEqual(lead.industry_code, "logistics")
        self.assertEqual(lead.campaign_code, "LOGISTICS_AI")
        self.assertGreaterEqual(lead.lead_score, 60)

    def test_campaign_is_server_resolved_and_unknown_industry_rejected(self):
        payload = lead_payload(industry="legal", solution="legal_ai_receptionist")
        payload["industry_campaign_code"] = "ATTACKER_SELECTED_CAMPAIGN"
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/v1/leads", payload, format="json", HTTP_IDEMPOTENCY_KEY="legal-route")
        self.assertEqual(response.status_code, 202)
        lead = LeadSubmission.objects.get()
        self.assertEqual((lead.industry_code, lead.campaign_code, lead.solution_code), ("legal", "LEGAL_AI", "legal_ai_receptionist"))
        invalid = self.client.post("/api/v1/leads", lead_payload(industry="arbitrary"), format="json", HTTP_IDEMPOTENCY_KEY="bad-route")
        self.assertEqual(invalid.status_code, 400)

    def test_all_expansion_campaigns_are_authoritative(self):
        expected = {
            "education":"EDUCATION_AI", "dental":"DENTAL_AI", "veterinary":"VETERINARY_AI",
            "automotive":"AUTOMOTIVE_AI", "restaurant":"RESTAURANT_AI", "manufacturing":"MANUFACTURING_AI",
            "recruitment":"RECRUITMENT_AI", "nonprofit":"NONPROFIT_AI", "public_services":"PUBLIC_SERVICES_AI",
            "energy":"ENERGY_AI", "telecom_it":"TELECOM_IT_AI", "wellness":"WELLNESS_AI",
            "security_services":"SECURITY_SERVICES_AI", "marketing_media":"MARKETING_MEDIA_AI",
            "gaming_entertainment":"GAMING_ENTERTAINMENT_AI",
        }
        for index, (industry, campaign) in enumerate(expected.items()):
            cache.clear()
            payload = lead_payload(industry=industry, work_email=f"expansion-{index}@example.com", phone_number=f"+1555011{index:04d}", solution=f"{industry}_ai_platform")
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/api/v1/leads", payload, format="json", HTTP_IDEMPOTENCY_KEY=f"expansion-{industry}")
            self.assertEqual(response.status_code, 202)
            lead = LeadSubmission.objects.get(work_email=payload["work_email"])
            self.assertEqual(lead.campaign_code, campaign)
            self.assertEqual(lead.team_code, "INDUSTRY_AI_SALES")
            self.assertEqual(lead.source_code, "CODESTRA_WEBSITE")

    def test_idempotency_replays_original_response(self):
        self.client.post("/api/v1/leads", lead_payload(), format="json", HTTP_IDEMPOTENCY_KEY="same-request")
        response = self.client.post("/api/v1/leads", lead_payload(), format="json", HTTP_IDEMPOTENCY_KEY="same-request")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LeadSubmission.objects.count(), 1)

    def test_duplicate_lead_is_rejected(self):
        self.client.post("/api/v1/leads", lead_payload(), format="json", HTTP_IDEMPOTENCY_KEY="first-request")
        response = self.client.post("/api/v1/leads", lead_payload(), format="json", HTTP_IDEMPOTENCY_KEY="second-request")
        self.assertEqual(response.status_code, 409)

    def test_consent_and_honeypot_are_enforced(self):
        no_consent = self.client.post("/api/v1/leads", lead_payload(consent=False), format="json", HTTP_IDEMPOTENCY_KEY="no-consent")
        bot = self.client.post("/api/v1/leads", lead_payload(honeypot="filled"), format="json", HTTP_IDEMPOTENCY_KEY="bot")
        self.assertEqual(no_consent.status_code, 400)
        self.assertEqual(bot.status_code, 400)

    @override_settings(
        LEAD_DELIVERY_MODE="production",
        ODOO_BASE_URL="https://odoo-stage.example.invalid",
        ODOO_DATABASE="codestra_stage",
        ODOO_CLIENT_ID="stage-client",
        ODOO_CLIENT_SECRET="stage-secret",
        ODOO_FIELD_MAPPING_CONFIRMED=True,
        ODOO_ROUTING_MAP={"LOGISTICS_AI": {"campaign_id": 11, "team_id": 22, "source_id": 33, "medium_id": 44}},
        **TEST_RUNTIME,
    )
    @patch("lead_capture.adapters.requests.post")
    def test_approved_submission_maps_to_crm_lead(self, post):
        post.return_value = Mock(status_code=201, json=lambda: {"id": 9876})
        lead = LeadSubmission.objects.create(
            idempotency_key_hash="e" * 64, duplicate_fingerprint="f" * 64,
            full_name="Ada Example", business_name="Example Logistics", work_email="ada-stage@example.com",
            phone_number="+15550100200", country="US", preferred_language="English", industry="Transportation",
            campaign_code="LOGISTICS_AI", employee_count="11-50", monthly_call_volume="1000-5000",
            product_interest="Dispatch automation", message="After-hours quote intake", consent=True,
            anonymous_session_id="stage-session",
        )
        with self.captureOnCommitCallbacks(execute=True):
            deliver_lead.run(lead.pk)
        lead.refresh_from_db()
        self.assertEqual(lead.delivery_status, "delivered")
        self.assertEqual(lead.delivery_reference, "9876")
        request = post.call_args
        self.assertTrue(request.args[0].endswith("/api/v1/models/crm.lead"))
        body = request.kwargs["json"]
        self.assertEqual(body["values"]["name"], "AI Receptionist — Example Logistics")
        self.assertEqual(body["values"]["email_from"], "ada-stage@example.com")
        self.assertEqual(body["campaign_id"], 11)

    def test_localization_context_uses_stable_locale_values(self):
        payload = lead_payload(
            preferred_language="es",
            content_locale="es",
            country_code="DO",
            locale_source="user_selection",
            translation_version="catalog-2026-08",
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/v1/leads", payload, format="json", HTTP_IDEMPOTENCY_KEY="localized-lead")
        self.assertEqual(response.status_code, 202)
        lead = LeadSubmission.objects.get()
        self.assertEqual(
            (lead.preferred_language, lead.content_locale, lead.country_code, lead.locale_source, lead.translation_version),
            ("es", "es", "DO", "user_selection", "catalog-2026-08"),
        )


@override_settings(**TEST_RUNTIME)
class LocalizationApiTests(APITestCase):
    def test_config_and_catalog_contracts(self):
        config = self.client.get("/api/v1/localization/config")
        messages = self.client.get("/api/v1/localization/messages/fr")
        unsupported = self.client.get("/api/v1/localization/messages/ht")
        self.assertEqual(config.status_code, 200)
        self.assertEqual(tuple(config.data["supported_locales"]), ("en", "es", "fr"))
        self.assertEqual(messages.data["catalog_delivery"], "bundled")
        self.assertEqual(unsupported.status_code, 404)

    def test_explicit_preference_is_validated_and_http_only(self):
        accepted = self.client.post("/api/v1/localization/preference", {"locale": "fr"}, format="json")
        rejected = self.client.post("/api/v1/localization/preference", {"locale": "arbitrary"}, format="json")
        self.assertEqual(accepted.status_code, 202)
        self.assertTrue(accepted.cookies["codestra_locale"]["httponly"])
        self.assertEqual(rejected.status_code, 400)

    @patch("lead_capture.views._country_for_request", return_value="DO")
    def test_country_response_is_minimal_and_never_returns_ip(self, _country):
        response = self.client.get("/api/v1/localization/country", REMOTE_ADDR="203.0.113.10")
        self.assertEqual(response.data, {"country_code": "DO", "suggested_locale": "es", "supported": True})
        self.assertNotIn("ip", response.data)

    def test_forwarded_address_is_used_only_for_configured_trusted_proxy(self):
        request = Mock()
        request.META = {"REMOTE_ADDR": "203.0.113.20", "HTTP_X_FORWARDED_FOR": "198.51.100.8, 10.0.0.1"}
        with mock.patch.dict("os.environ", {"TRUSTED_PROXY_IPS": "203.0.113.0/24"}):
            self.assertEqual(_client_ip(request), "198.51.100.8")
        with mock.patch.dict("os.environ", {"TRUSTED_PROXY_IPS": "192.0.2.5"}):
            self.assertEqual(_client_ip(request), "203.0.113.20")


@override_settings(**TEST_RUNTIME)
class DeliveryFailureTests(APITestCase):
    @override_settings(
        LEAD_DELIVERY_MODE="production",
        ODOO_BASE_URL="https://odoo.example",
        ODOO_DATABASE="codestra",
        ODOO_CLIENT_ID="client",
        ODOO_CLIENT_SECRET="secret",
        ODOO_FIELD_MAPPING_CONFIRMED=True,
        ODOO_ROUTING_MAP={"": {"campaign_id": 1, "team_id": 2, "source_id": 3, "medium_id": 4}},
    )
    @patch("lead_capture.adapters.requests.post")
    def test_odoo_timeout_is_retried_and_not_exposed(self, post):
        post.side_effect = requests.Timeout("private upstream detail")
        lead = LeadSubmission.objects.create(
            idempotency_key_hash="a" * 64,
            duplicate_fingerprint="b" * 64,
            full_name="Timeout Test", business_name="Example", work_email="timeout@example.com",
            phone_number="+15550100200", country="US", preferred_language="English",
            industry="Services", employee_count="1-10", monthly_call_volume="Under 500",
            product_interest="AI Receptionist", consent=True, anonymous_session_id="session-timeout",
        )
        with self.assertRaises(requests.Timeout):
            deliver_lead.run(lead.pk)
        self.assertNotIn("private upstream detail", lead.delivery_error_code)

    @override_settings(LEAD_DELIVERY_MODE="production", ODOO_FIELD_MAPPING_CONFIRMED=False)
    def test_unapproved_odoo_mapping_fails_closed(self):
        lead = LeadSubmission.objects.create(
            idempotency_key_hash="c" * 64,
            duplicate_fingerprint="d" * 64,
            full_name="Config Test", business_name="Example", work_email="config@example.com",
            phone_number="+15550100201", country="US", preferred_language="English",
            industry="Services", employee_count="1-10", monthly_call_volume="Under 500",
            product_interest="AI Receptionist", consent=True, anonymous_session_id="session-config",
        )
        deliver_lead.run(lead.pk)
        lead.refresh_from_db()
        self.assertEqual(lead.delivery_status, "failed")
        self.assertEqual(lead.delivery_error_code, "odoo_not_approved")


@override_settings(**TEST_RUNTIME)
class AnalyticsEventTests(APITestCase):
    def test_privacy_safe_event_is_accepted_and_unknown_fields_are_not_stored(self):
        response = self.client.post("/api/v1/analytics/events", {
            "event_name": "cta_click",
            "anonymous_session_id": "session-analytics",
            "occurred_at": "2026-08-02T12:00:00Z",
            "page_path": "/ai-receptionist",
            "cta_name": "Book a Live Demo",
            "section": "hero",
            "attribution": {"utm_source": "newsletter", "email": "must-not-store@example.com"},
            "device_category": "desktop",
            "language": "en",
            "consent_state": "granted",
        }, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(AnalyticsEvent.objects.get().attribution, {"utm_source": "newsletter"})

    def test_public_industry_and_operational_boundaries(self):
        directory = self.client.get("/api/v1/public/industries")
        logistics = self.client.get("/api/v1/public/industries/logistics-ai")
        availability = self.client.get("/api/v1/public/availability")
        live = self.client.get("/health/live")
        ready = self.client.get("/health/ready")
        manifest = self.client.get("/.well-known/codestra-service")
        metrics = self.client.get("/metrics")
        self.assertEqual(directory.status_code, 200)
        self.assertEqual(logistics.data["campaign"], "LOGISTICS_AI")
        self.assertFalse(availability.data["live_workflows"])
        self.assertEqual(live.status_code, 200)
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(manifest.data["delivery_mode"], "mock")
        self.assertIn(metrics.status_code, (401, 403))

    def test_public_contracts_and_internal_boundary(self):
        self.assertEqual(self.client.get("/api/v1/public/integrations").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/public/demo-scenarios/legal").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/consent", {"state": "granted", "policy_version": "2026-08"}, format="json").status_code, 202)
        roi = self.client.post("/api/v1/roi-calculations", {"volume": 1000, "missed_percent": 20, "lead_value": 100, "conversion_percent": 10}, format="json")
        self.assertEqual(roi.data["monthly_opportunity"], 2000)
        self.assertEqual(self.client.get("/internal/v1/odoo/reconciliation/failures").status_code, 401)
