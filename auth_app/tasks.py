import logging
from celery import shared_task
from django.utils import timezone
from helpers.middleware_client import MiddlewareConfigurationError, MiddlewareRequestError, submit_contact
from .models import User

logger = logging.getLogger(__name__)

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
        operation = submit_contact(payload, idempotency_key=f"codestra-signup-{user.pk}")
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

    operation_id = str(operation.get("operation_id") or operation.get("command_id") or "")[:128]
    user.crm_sync_status = "synced"
    user.crm_sync_operation_id = operation_id
    user.crm_sync_last_error = ""
    user.crm_synced_at = timezone.now()
    user.save(update_fields=["crm_sync_status","crm_sync_operation_id","crm_sync_last_error","crm_synced_at"])
    return {"status": "synced", "operation_id": operation_id}
