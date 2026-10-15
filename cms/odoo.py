import logging


from helpers.middleware_client import (
    MiddlewareConfigurationError,
    MiddlewareRequestError,
    accepted_operation_id,
    submit_contact,
    submit_opportunity,
)

logger = logging.getLogger(__name__)


def _deliver(instance, sender, payload, *, idempotency_key):
    try:
        response_data = sender(payload, idempotency_key=idempotency_key)
        operation_id = accepted_operation_id(response_data)
        instance.odoo_sync_status = "submitted"
        instance.odoo_record_id = operation_id
        instance.odoo_last_error = ""
        instance.odoo_synced_at = None
        instance.save(
            update_fields=[
                "odoo_sync_status",
                "odoo_record_id",
                "odoo_last_error",
                "odoo_synced_at",
            ]
        )
        return True
    except MiddlewareConfigurationError:
        instance.odoo_sync_status = "pending"
        instance.odoo_last_error = "Middleware integration is not configured"
        instance.save(update_fields=["odoo_sync_status", "odoo_last_error"])
        return False
    except MiddlewareRequestError:
        instance.odoo_sync_status = "failed"
        instance.odoo_last_error = "Middleware delivery failed"
        instance.save(update_fields=["odoo_sync_status", "odoo_last_error"])
        logger.warning(
            "Middleware delivery failed for %s %s",
            instance._meta.label,
            instance.pk,
        )
        return False


def sync_contact(contact):
    return _deliver(
        contact,
        submit_opportunity,
        {
            "full_name": contact.full_name,
            "email": contact.email,
            "company_size": contact.company_size,
            "message": contact.message,
            "source": "codestra-contact-sales",
        },
        idempotency_key=f"codestra-contact-{contact.pk}",
    )


def sync_billing_interest(interest):
    return _deliver(
        interest,
        submit_opportunity,
        {
            "full_name": interest.full_name,
            "email": interest.email,
            "phone": interest.phone,
            "uses_erp": interest.uses_erp,
            "consent_to_contact": interest.consent_to_contact,
            "source": interest.source,
            "message": "Electronic billing consultation",
        },
        idempotency_key=f"codestra-billing-interest-{interest.pk}",
    )


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
    return _deliver(
        taxpayer,
        submit_contact,
        payload,
        idempotency_key=f"codestra-taxpayer-{taxpayer.pk}",
    )
