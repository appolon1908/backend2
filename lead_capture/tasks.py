import logging

import requests
from celery import shared_task
from django.utils import timezone

from .adapters import DeliveryConfigurationError, get_lead_adapter
from .models import LeadSubmission


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(requests.Timeout, requests.ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def deliver_lead(self, lead_id):
    lead = LeadSubmission.objects.get(pk=lead_id)
    lead.delivery_attempts += 1
    try:
        lead.delivery_reference = get_lead_adapter().deliver(lead)
        lead.delivery_status = LeadSubmission.DeliveryStatus.DELIVERED
        lead.delivery_error_code = ""
        lead.delivered_at = timezone.now()
    except (requests.Timeout, requests.ConnectionError):
        lead.delivery_status = LeadSubmission.DeliveryStatus.DEAD_LETTER if self.request.retries >= self.max_retries else LeadSubmission.DeliveryStatus.QUEUED
        lead.delivery_error_code = "temporary_upstream_failure"
        logger.warning("Temporary lead delivery failure request_id=%s attempt=%s", lead.request_id, lead.delivery_attempts)
        if lead.delivery_status != LeadSubmission.DeliveryStatus.DEAD_LETTER:
            raise
    except DeliveryConfigurationError as exc:
        lead.delivery_status = LeadSubmission.DeliveryStatus.FAILED
        lead.delivery_error_code = str(exc)[:64]
        logger.warning("Lead delivery configuration failure request_id=%s", lead.request_id)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 0
        lead.delivery_status = LeadSubmission.DeliveryStatus.FAILED
        lead.delivery_error_code = f"odoo_http_{status_code}"
        logger.warning("Lead delivery HTTP failure request_id=%s status=%s", lead.request_id, status_code)
        if status_code >= 500:
            raise
    finally:
        lead.save(update_fields=["delivery_attempts", "delivery_reference", "delivery_status", "delivery_error_code", "delivered_at", "updated_at"])
    return lead.delivery_status
