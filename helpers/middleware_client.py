import logging
from uuid import UUID

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MiddlewareConfigurationError(RuntimeError):
    pass


class MiddlewareRequestError(RuntimeError):
    pass


class MiddlewareResponseError(MiddlewareRequestError):
    pass


def _config():
    base_url = getattr(settings, "MIDDLEWARE_BASE_URL", "").rstrip("/")
    token = getattr(settings, "MIDDLEWARE_ACCESS_TOKEN", "")
    tenant_id = getattr(settings, "MIDDLEWARE_TENANT_ID", "")
    if not base_url or not token or not tenant_id:
        raise MiddlewareConfigurationError("Middleware integration is not configured")
    return base_url, token, tenant_id


def accepted_operation_id(body):
    """Validate an operation receipt without claiming provider readback."""
    if not isinstance(body, dict):
        raise MiddlewareResponseError("Middleware returned an invalid operation receipt")
    value = body.get("operation_id")
    state = body.get("state")
    try:
        operation_id = str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MiddlewareResponseError("Middleware returned an invalid operation receipt") from exc
    if not isinstance(state, str) or state.upper() not in {
        "RECEIVED", "QUEUED", "SUBMITTED", "ACCEPTED", "UNKNOWN", "COMPLETED",
    }:
        raise MiddlewareResponseError("Middleware did not accept the operation")
    return operation_id


def _post(path, payload, *, idempotency_key):
    base_url, token, tenant_id = _config()
    try:
        response = requests.post(
            f"{base_url}{path}",
            params={"tenant_id": tenant_id},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MiddlewareRequestError("Middleware request failed") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise MiddlewareResponseError("Middleware returned invalid JSON") from exc

    if not isinstance(body, dict):
        raise MiddlewareResponseError("Middleware returned an invalid response")
    accepted_operation_id(body)
    return body


def submit_contact(payload, *, idempotency_key):
    return _post("/platform/v1/contacts", payload, idempotency_key=idempotency_key)


def submit_opportunity(payload, *, idempotency_key):
    return _post("/platform/v1/opportunities", payload, idempotency_key=idempotency_key)


def submit_contact_task(contact_id, payload, *, idempotency_key):
    return _post(
        f"/platform/v1/contacts/{int(contact_id)}/tasks",
        payload,
        idempotency_key=idempotency_key,
    )
