import logging

import requests
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


def _record_id(response_data):
    if not isinstance(response_data, dict):
        return ""
    value = response_data.get("id") or response_data.get("lead_id") or response_data.get("result", {}).get("id")
    return str(value or "")[:128]


def send_to_odoo(instance, endpoint, payload):
    """Attempt delivery once while keeping the locally saved submission authoritative."""
    if not settings.ODOO_API_TOKEN or not settings.ODOO_BASE_URL:
        instance.odoo_sync_status = "pending"
        instance.odoo_last_error = "Odoo integration is not configured"
        instance.save(update_fields=["odoo_sync_status", "odoo_last_error"])
        return False

    try:
        response = requests.post(
            f"{settings.ODOO_BASE_URL}/{endpoint.lstrip('/')}",
            headers={"Authorization": f"Bearer {settings.ODOO_API_TOKEN}"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        try:
            response_data = response.json()
        except ValueError:
            response_data = {}
        instance.odoo_sync_status = "synced"
        instance.odoo_record_id = _record_id(response_data)
        instance.odoo_last_error = ""
        instance.odoo_synced_at = timezone.now()
        instance.save(update_fields=["odoo_sync_status", "odoo_record_id", "odoo_last_error", "odoo_synced_at"])
        return True
    except requests.RequestException as exc:
        instance.odoo_sync_status = "failed"
        instance.odoo_last_error = str(exc)[:1000]
        instance.save(update_fields=["odoo_sync_status", "odoo_last_error"])
        logger.warning("Odoo delivery failed for %s %s", instance._meta.label, instance.pk)
        return False


def sync_contact(contact):
    return send_to_odoo(contact, "crm/lead/create", {
        "full_name": contact.full_name,
        "email": contact.email,
        "company_size": contact.company_size,
        "message": contact.message,
        "source": "codestra-contact-sales",
    })


def sync_billing_interest(interest):
    return send_to_odoo(interest, "crm/lead/create", {
        "full_name": interest.full_name,
        "email": interest.email,
        "phone": interest.phone,
        "uses_erp": interest.uses_erp,
        "consent_to_contact": interest.consent_to_contact,
        "source": interest.source,
        "message": "Electronic billing consultation",
    })


def sync_taxpayer(taxpayer):
    payload = {
        "taxpayer_rnc": taxpayer.tax_payer_rnc,
        "taxpayer_name": taxpayer.name_of_tax_payer,
        "trade_name": taxpayer.trade_name,
        "taxpayer_telephone": taxpayer.tax_payer_telephone,
        "taxpayer_cell_phone": taxpayer.tax_payer_cell_phone,
        "taxpayer_email": taxpayer.tax_payer_email,
        "taxpayer_number": taxpayer.tax_payer_number,
        "taxpayer_sector": taxpayer.tax_payer_sector,
        "taxpayer_province": taxpayer.tax_payer_province,
        "address_reference": taxpayer.address_reference,
        "visiting_hours": taxpayer.visiting_hours,
        "representation_rnc": taxpayer.representation_rnc,
        "name_of_representative": taxpayer.name_of_representative,
        "representative_phone": taxpayer.representative_phone,
        "representative_cell_phone": taxpayer.representative_cell_phone,
        "representative_email": taxpayer.representative_email,
        "operation_carried_out_in_premise": taxpayer.operation_carried_out_in_premise,
        "street_of_warehouse": taxpayer.street_of_warehouse,
        "store_or_warehouse_number": taxpayer.store_or_warehouse_number,
        "province_of_warehouse": taxpayer.province_of_warehouse,
        "warehouse_reference": taxpayer.warehouse_reference,
        "local_administration": taxpayer.local_administration,
        "warehouse_sector": taxpayer.warehouse_sector,
        "source": "codestra-taxpayer-registration",
    }
    return send_to_odoo(taxpayer, "contribuyente/register", payload)
