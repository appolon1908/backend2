"""Read-only Odoo 20 CRM bridge for Codestra's authenticated staff dashboard.

The browser never sees the Odoo API key. This backend only forwards the three
explicitly versioned, read-only resource paths; it does not expose a general
proxy, forward user-controlled URLs, or enable external provider effects.
"""
from urllib.parse import urlparse

import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission

CRM_ADMIN_GROUP = "Codestra Call Center Super User"


class CanViewCodestraCRM(BasePermission):
    """A Codestra staff login alone is not sufficient to view CRM records."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.is_staff
            and (
                user.is_superuser
                or user.groups.filter(name=CRM_ADMIN_GROUP).exists()
            )
        )

from rest_framework.response import Response


ODOO_RESOURCES = {
    "overview": "/callcenter/api/v1/overview",
    "campaigns": "/callcenter/api/v1/campaigns",
    "leads": "/callcenter/api/v1/leads",
}


def _pagination(request):
    params = {}
    for field, upper in (("page", 100000), ("limit", 50), ("campaign_id", 2147483647)):
        raw = request.query_params.get(field)
        if raw in (None, ""):
            continue
        if not raw.isdecimal() or not 1 <= int(raw) <= upper:
            raise ValueError(f"Invalid {field}")
        params[field] = int(raw)
    return params


def _fetch_odoo(resource, params):
    base_url = str(getattr(settings, "ODOO_BASE_URL", "") or "").rstrip("/")
    token = str(getattr(settings, "ODOO_API_TOKEN", "") or "")
    parsed = urlparse(base_url)
    if not token or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"error": "odoo_not_configured", "message": "CRM integration is not configured."}, 503
    # Public traffic must use HTTPS; private Docker/LAN deployments can opt into
    # HTTP only when addressed by an RFC1918/private service hostname.
    if parsed.scheme == "http" and parsed.hostname not in {
        "odoo", "compose-odoo-1", "localhost", "127.0.0.1"
    }:
        return {"error": "odoo_insecure_transport"}, 503
    try:
        response = requests.get(
            base_url + ODOO_RESOURCES[resource],
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params=params,
            timeout=(3, 10),
            allow_redirects=False,
        )
    except requests.RequestException:
        return {"error": "odoo_unreachable", "message": "CRM service is temporarily unavailable."}, 503
    if response.status_code in (401, 403):
        return {"error": "odoo_auth_failed", "message": "CRM service authorization failed."}, 503
    if response.status_code != 200 or "application/json" not in response.headers.get("Content-Type", ""):
        return {"error": "odoo_invalid_response", "message": "CRM service did not return its API contract."}, 502
    try:
        result = response.json()
    except ValueError:
        result = None
    if not isinstance(result, dict) or result.get("schema_version") != 1:
        return {"error": "odoo_contract_mismatch", "message": "CRM service returned an unsupported response."}, 502
    if result.get("role") != "superuser":
        return {
            "error": "odoo_service_role_mismatch",
            "message": "The configured Odoo account is not a Call Center Super User.",
        }, 503
    expected_collection = {"campaigns": "campaigns", "leads": "leads"}.get(resource)
    if expected_collection and not isinstance(result.get(expected_collection), list):
        return {
            "error": "odoo_contract_mismatch",
            "message": "CRM service returned invalid resource data.",
        }, 502
    return result, 200


class OdooCRMReadViewSet(viewsets.ViewSet):
    """Staff-only data, then Odoo's own record rules on the API-key user."""

    permission_classes = (CanViewCodestraCRM,)
    http_method_names = ("get", "head", "options")

    def _read(self, request, resource):
        if resource == "overview":
            params = {}
        else:
            try:
                params = _pagination(request)
            except ValueError:
                return Response({"error": "invalid_query"}, status=status.HTTP_400_BAD_REQUEST)
            if resource == "campaigns":
                params.pop("campaign_id", None)
        payload, code = _fetch_odoo(resource, params)
        result = Response(payload, status=code)
        result["Cache-Control"] = "private, no-store, max-age=0"
        return result

    @action(detail=False, methods=["get"])
    def overview(self, request):
        return self._read(request, "overview")

    @action(detail=False, methods=["get"])
    def campaigns(self, request):
        return self._read(request, "campaigns")

    @action(detail=False, methods=["get"])
    def leads(self, request):
        return self._read(request, "leads")
