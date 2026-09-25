import hashlib
import hmac
import json
import time

import requests
from celery import shared_task
from django.utils import timezone

from .models import WebhookDelivery


def signature(secret, timestamp, body):
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def deliver_webhook(self, delivery_id):
    delivery = WebhookDelivery.objects.select_related("subscription").get(pk=delivery_id)
    if not delivery.subscription.enabled:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.error = "subscription_disabled"
        delivery.save(update_fields=["status", "error", "updated_at"])
        return delivery.status
    body = json.dumps({"id": str(delivery.event_id), "type": delivery.event_type, "data": delivery.payload}, separators=(",", ":")).encode()
    timestamp = int(time.time())
    delivery.attempts += 1
    delivery.attempt_history.append({"attempt": delivery.attempts, "started_at": timezone.now().isoformat()})
    try:
        secret = delivery.subscription.current_secret()
        response = requests.post(delivery.subscription.url, data=body, headers={"Content-Type": "application/json", "X-Codestra-Signature": signature(secret, timestamp, body), "X-Codestra-Event-Id": str(delivery.event_id)}, timeout=8, allow_redirects=False, stream=True)
        delivery.response_code = response.status_code
        delivery.response_body = response.raw.read(65536, decode_content=True).decode("utf-8", errors="replace")[:1000]
        if 200 <= response.status_code < 300:
            delivery.status = WebhookDelivery.Status.DELIVERED
            delivery.delivered_at = timezone.now()
            delivery.error = ""
            delivery.attempt_history[-1].update({"status": "delivered", "response_code": response.status_code})
        elif response.status_code >= 500 and self.request.retries < self.max_retries:
            delivery.status = WebhookDelivery.Status.RETRYING
            delivery.error = "receiver_5xx"
            delivery.attempt_history[-1].update({"status": "retrying", "response_code": response.status_code})
            delivery.save(update_fields=["attempts", "attempt_history", "response_code", "response_body", "status", "error", "updated_at"])
            raise self.retry()
        else:
            delivery.status = WebhookDelivery.Status.FAILED
            delivery.error = "receiver_rejected"
            delivery.attempt_history[-1].update({"status": "failed", "response_code": response.status_code})
    except (requests.Timeout, requests.ConnectionError) as exc:
        delivery.error = "receiver_unavailable"
        delivery.status = WebhookDelivery.Status.RETRYING if self.request.retries < self.max_retries else WebhookDelivery.Status.FAILED
        delivery.attempt_history[-1].update({"status": delivery.status, "error": delivery.error})
        delivery.save(update_fields=["attempts", "attempt_history", "status", "error", "updated_at"])
        if delivery.status == WebhookDelivery.Status.RETRYING:
            raise self.retry(exc=exc)
    delivery.save(update_fields=["attempts", "attempt_history", "response_code", "response_body", "status", "error", "delivered_at", "updated_at"])
    return delivery.status
