import uuid

import requests
from django.conf import settings

from .odoo_mapping import CUSTOM_FIELDS_TO_CONFIRM, STANDARD_FIELDS


class DeliveryConfigurationError(RuntimeError):
    pass


class MockLeadAdapter:
    def deliver(self, lead):
        return f"mock-{lead.request_id}"


class OdooLeadAdapter:
    """Production boundary. Disabled until credentials and custom mappings are confirmed."""

    def deliver(self, lead):
        required = (
            settings.ODOO_BASE_URL,
            settings.ODOO_DATABASE,
            settings.ODOO_CLIENT_ID,
            settings.ODOO_CLIENT_SECRET,
        )
        if not all(required) or not settings.ODOO_FIELD_MAPPING_CONFIRMED:
            raise DeliveryConfigurationError("odoo_not_approved")
        route = settings.ODOO_ROUTING_MAP.get(lead.campaign_code, {})
        if not all(route.get(key) for key in ("campaign_id", "team_id", "source_id", "medium_id")):
            raise DeliveryConfigurationError("odoo_route_not_confirmed")

        source = {
            "lead_title": f"AI Receptionist — {lead.business_name}",
            "full_name": lead.full_name,
            "business_name": lead.business_name,
            "work_email": lead.work_email,
            "phone_number": lead.phone_number,
            "description": lead.message,
            "lead_type": "lead",
            "preferred_language": lead.preferred_language,
            "industry": lead.industry,
            "monthly_call_volume": lead.monthly_call_volume,
            "product_interest": lead.product_interest,
            "preferred_demo_time": " ".join(filter(None, [str(lead.preferred_demo_date or ""), str(lead.preferred_demo_time or "")])),
            "consent": lead.consent,
            "cta_clicked": lead.cta_clicked,
            "attribution": lead.attribution,
        }
        values = {field: source[key] for field, key in {**STANDARD_FIELDS, **CUSTOM_FIELDS_TO_CONFIRM}.items()}
        response = requests.post(
            f"{settings.ODOO_BASE_URL}/api/v1/models/{settings.ODOO_LEAD_MODEL}",
            headers={
                "X-Odoo-Database": settings.ODOO_DATABASE,
                "X-Client-Id": settings.ODOO_CLIENT_ID,
                "X-Client-Secret": settings.ODOO_CLIENT_SECRET,
                "Idempotency-Key": str(lead.request_id),
            },
            json={"values": values, "team_id": route["team_id"], "campaign_id": route["campaign_id"], "source_id": route["source_id"], "medium_id": route["medium_id"], "user_id": route.get("user_id")},
            timeout=settings.ODOO_REQUEST_TIMEOUT_MS / 1000,
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("id") or data.get("result") or uuid.uuid4())[:128]


def get_lead_adapter():
    if settings.LEAD_DELIVERY_MODE == "mock":
        return MockLeadAdapter()
    if settings.LEAD_DELIVERY_MODE == "production":
        return OdooLeadAdapter()
    raise DeliveryConfigurationError("invalid_delivery_mode")
