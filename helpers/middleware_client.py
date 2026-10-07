import logging
from uuid import uuid4

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MiddlewareConfigurationError(RuntimeError):
    pass


class MiddlewareRequestError(RuntimeError):
    pass


def _config():
    base_url = getattr(settings, "MIDDLEWARE_BASE_URL", "").rstrip("/")
    token = getattr(settings, "MIDDLEWARE_ACCESS_TOKEN", "")
    tenant_id = getattr(settings, "MIDDLEWARE_TENANT_ID", "")
    if not base_url or not token or not tenant_id:
        raise MiddlewareConfigurationError("Middleware integration is not configured")
    return base_url, token, tenant_id


def _post(path, payload, *, idempotency_key):
    base_url, token, tenant_id = _config()
    correlation_id = str(uuid4())
    try:
        response = requests.post(
            f"{base_url}{path}",
            params={"tenant_id": tenant_id},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
                "X-Correlation-ID": correlation_id,
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
        raise MiddlewareRequestError("Middleware returned invalid JSON") from exc

    if not isinstance(body, dict):
        raise MiddlewareRequestError("Middleware returned an invalid response")
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
