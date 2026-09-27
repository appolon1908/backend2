import hashlib
import hmac
import json

import requests
from django.conf import settings


class GatewayUnavailable(RuntimeError):
    pass


def hash_idempotency(value):
    return hashlib.sha256(value.encode()).hexdigest()


def dispatch(path, payload, headers):
    if not settings.MIDDLEWARE_GATEWAY_URL:
        raise GatewayUnavailable("middleware_gateway_not_configured")
    safe_headers = {
        "Authorization": headers.get("Authorization", ""),
        "Idempotency-Key": headers["Idempotency-Key"],
        "X-Tenant-ID": headers["X-Tenant-ID"],
        "X-Workspace-ID": headers["X-Workspace-ID"],
        "X-Audit-Context": headers.get("X-Audit-Context", "{}"),
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{settings.MIDDLEWARE_GATEWAY_URL.rstrip('/')}/{path.lstrip('/')}",
        data=json.dumps(payload), headers=safe_headers, timeout=settings.MIDDLEWARE_GATEWAY_TIMEOUT,
        allow_redirects=False,
    )
    if response.status_code >= 500:
        raise GatewayUnavailable("middleware_gateway_failure")
    return response


def constant_time_checksum(expected, actual):
    return bool(expected) and hmac.compare_digest(expected.lower(), actual.lower())
