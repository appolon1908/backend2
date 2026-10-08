import logging

from celery import shared_task
from django.db import transaction

from helpers.middleware_client import (
    MiddlewareConfigurationError,
    MiddlewareRequestError,
    MiddlewareResponseError,
    _config,
    accepted_operation_id,
    submit_contact,
)
from .models import User, Visitor

logger = logging.getLogger(__name__)


@shared_task
def log_visitor_details(visitor_data):
    """Retain the task imported by the production visitor middleware."""
    visitor = Visitor.objects.create(
        ip_address=visitor_data.get("ip_address"),
        page=visitor_data.get("page"),
        device=visitor_data.get("device"),
        os=visitor_data.get("os"),
        browser=visitor_data.get("browser"),
        method=visitor_data.get("method"),
        visited_at=visitor_data.get("visited_at"),
    )
    return {"status": "saved", "visitor_id": visitor.pk}


def signup_payload(user):
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone_number,
        "plan_type": user.plan_type,
        "source": "codestra-signup",
    }


def queue_signup_sync(user_id):
    """The database intent survives absent configuration or an unavailable broker."""
    try:
        _config()
    except MiddlewareConfigurationError:
        User.objects.filter(pk=user_id, crm_sync_operation_id="").update(
            crm_sync_status="pending",
            crm_sync_last_error="Middleware integration is not configured",
        )
        return False
    try:
        sync_signup_to_middleware.delay(user_id)
    except Exception:
        User.objects.filter(pk=user_id, crm_sync_operation_id="").update(
            crm_sync_status="pending",
            crm_sync_last_error="Background delivery is unavailable; pending recovery",
        )
        logger.warning("Signup queue unavailable for user %s", user_id)
        return False
    return True


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def sync_signup_to_middleware(self, user_id):
    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(pk=user_id)
        except User.DoesNotExist:
            return {"status": "discarded", "reason": "user_not_found"}
        if user.crm_sync_operation_id:
            return {"status": user.crm_sync_status, "operation_id": user.crm_sync_operation_id}
        if not user.crm_sync_payload:
            # Freeze legacy pending intents before their first delivery attempt.
            user.crm_sync_payload = signup_payload(user)
            user.save(update_fields=["crm_sync_payload"])
        payload = dict(user.crm_sync_payload)

    try:
        operation = submit_contact(payload, idempotency_key=f"codestra-signup-{user.pk}")
        operation_id = accepted_operation_id(operation)
    except MiddlewareConfigurationError:
        User.objects.filter(pk=user.pk, crm_sync_operation_id="").update(
            crm_sync_status="pending",
            crm_sync_last_error="Middleware integration is not configured",
        )
        return {"status": "pending"}
    except MiddlewareResponseError:
        User.objects.filter(pk=user.pk, crm_sync_operation_id="").update(
            crm_sync_status="failed",
            crm_sync_last_error="Middleware did not return an accepted operation",
        )
        return {"status": "failed"}
    except MiddlewareRequestError as exc:
        User.objects.filter(pk=user.pk, crm_sync_operation_id="").update(
            crm_sync_status="failed",
            crm_sync_last_error="Middleware delivery failed",
        )
        logger.warning("Signup Middleware delivery failed for user %s", user.pk)
        raise self.retry(exc=exc)

    # Acceptance is an operation receipt, not verified Odoo synchronization.
    User.objects.filter(pk=user.pk, crm_sync_operation_id="").update(
        crm_sync_status="submitted",
        crm_sync_operation_id=operation_id,
        crm_sync_last_error="",
        crm_synced_at=None,
    )
    return {"status": "submitted", "operation_id": operation_id}


def enqueue_signup_sync(user_id):
    """Keep main's enqueue entrypoint on the deployed, configuration-gated path."""
    return queue_signup_sync(user_id)


@shared_task
def enqueue_pending_signup_syncs(limit=100):
    """Recover only bounded, durable signup intents without replaying acceptance.

    The same eligibility rules are used by retry_pending_signups. Legacy users,
    already-linked Odoo accounts, and accepted operations are never swept in.
    No credentials configured means no queue activity and no external effects.
    """
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer between 1 and 1000")
    try:
        _config()
    except MiddlewareConfigurationError:
        return {"eligible": 0, "queued": 0}
    user_ids = list(
        User.objects.filter(
            crm_sync_status__in=("pending", "failed"),
            crm_sync_operation_id="",
            odoo_id__isnull=True,
        )
        .exclude(crm_sync_payload={})
        .order_by("created_at", "pk")
        .values_list("pk", flat=True)[:limit]
    )
    queued = sum(bool(queue_signup_sync(user_id)) for user_id in user_ids)
    return {"eligible": len(user_ids), "queued": queued}
