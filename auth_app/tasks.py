import logging

from celery import shared_task
from django.utils import timezone

from helpers.middleware_client import (
    MiddlewareConfigurationError,
    MiddlewareRequestError,
    submit_contact,
)
from .models import User, Visitor

logger = logging.getLogger(__name__)


@shared_task
def log_visitor_details(visitor_data):
    """Persist visitor telemetry queued by VisitorTrackingMiddleware."""
    visitor = Visitor(
        ip_address=visitor_data.get("ip_address"),
        page=visitor_data.get("page"),
        device=visitor_data.get("device"),
        os=visitor_data.get("os"),
        browser=visitor_data.get("browser"),
        method=visitor_data.get("method"),
        visited_at=visitor_data.get("visited_at"),
    )
    visitor.save()
    return {"status": "saved", "visitor_id": visitor.pk}


def enqueue_signup_sync(user_id):
    """Best-effort enqueue backed by durable user sync state.

    Broker failure cannot lose the work: the user stays pending and the
    periodic recovery task will enqueue it again after the broker recovers.
    """
    try:
        sync_signup_to_middleware.delay(user_id)
        return True
    except Exception:
        User.objects.filter(pk=user_id).update(
            crm_sync_status="pending",
            crm_sync_last_error="CRM sync enqueue failed; retry scheduled",
        )
        logger.exception("Failed to enqueue signup CRM sync for user %s", user_id)
        return False


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def sync_signup_to_middleware(self, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {"status": "discarded", "reason": "user_not_found"}

    payload = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone_number,
        "plan_type": user.plan_type,
        "source": "codestra-signup",
    }
    try:
        operation = submit_contact(
            payload,
            idempotency_key=f"codestra-signup-{user.pk}",
        )
    except MiddlewareConfigurationError:
        user.crm_sync_status = "pending"
        user.crm_sync_last_error = "Middleware integration is not configured"
        user.save(update_fields=["crm_sync_status", "crm_sync_last_error"])
        return {"status": "pending"}
    except MiddlewareRequestError as exc:
        user.crm_sync_status = "failed"
        user.crm_sync_last_error = "Middleware delivery failed"
        user.save(update_fields=["crm_sync_status", "crm_sync_last_error"])
        logger.warning("Signup Middleware delivery failed for user %s", user.pk)
        raise self.retry(exc=exc)

    operation_id = str(
        operation.get("operation_id") or operation.get("command_id") or ""
    )[:128]
    user.crm_sync_status = "synced"
    user.crm_sync_operation_id = operation_id
    user.crm_sync_last_error = ""
    user.crm_synced_at = timezone.now()
    user.save(
        update_fields=[
            "crm_sync_status",
            "crm_sync_operation_id",
            "crm_sync_last_error",
            "crm_synced_at",
        ]
    )
    return {"status": "synced", "operation_id": operation_id}


@shared_task
def enqueue_pending_signup_syncs(limit=100):
    """Recover durable pending/failed signup projections.

    This is intentionally bounded so one beat tick cannot flood the broker.
    """
    user_ids = list(
        User.objects.filter(crm_sync_status__in=("pending", "failed"))
        .order_by("created_at")
        .values_list("pk", flat=True)[:limit]
    )
    queued = 0
    for user_id in user_ids:
        if enqueue_signup_sync(user_id):
            queued += 1
    return {"eligible": len(user_ids), "queued": queued}
