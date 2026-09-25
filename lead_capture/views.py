import hashlib
import ipaddress
import os
from pathlib import Path

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from django.http import HttpResponse

from .models import AnalyticsEvent, LeadSubmission
from .serializers import AnalyticsEventSerializer, LeadSubmissionSerializer
from .tasks import deliver_lead
from .routing import INDUSTRIES

SUPPORTED_LOCALES = ("en", "es", "fr")
COUNTRY_LOCALES = {"DO": "es", "HT": "fr", "FR": "fr", "ES": "es", "MX": "es", "CO": "es"}


def _client_ip(request):
    remote = request.META.get("REMOTE_ADDR", "")
    trusted = []
    for item in os.getenv("TRUSTED_PROXY_IPS", "").split(","):
        try:
            trusted.append(ipaddress.ip_network(item.strip(), strict=False))
        except ValueError:
            continue
    try:
        proxy_ip = ipaddress.ip_address(remote)
    except ValueError:
        proxy_ip = None
    if proxy_ip and any(proxy_ip in network for network in trusted):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        candidate = forwarded.split(",")[0].strip() if forwarded else remote
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return remote
    return remote


def _country_for_request(request):
    database = Path(os.getenv("GEOIP_COUNTRY_DB", "/var/lib/geoip/GeoLite2-Country.mmdb"))
    if not database.is_file():
        return ""
    try:
        import geoip2.database
        with geoip2.database.Reader(str(database)) as reader:
            return (reader.country(_client_ip(request)).country.iso_code or "").upper()
    except Exception:
        return ""


class LocalizationConfigView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"supported_locales": SUPPORTED_LOCALES, "fallback_locale": "en", "country_detection": True})


class LocalizationCountryView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics_event"
    def get(self, request):
        country = _country_for_request(request)
        locale = COUNTRY_LOCALES.get(country)
        return Response({"country_code": country or None, "suggested_locale": locale, "supported": bool(locale)})


class LocalizationPreferenceView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        locale = request.data.get("locale")
        if locale not in SUPPORTED_LOCALES:
            return Response({"code": "unsupported_locale"}, status=400)
        response = Response({"accepted": True, "locale": locale}, status=202)
        response.set_cookie("codestra_locale", locale, max_age=31536000, secure=not settings.DEBUG,
                            httponly=True, samesite="Lax")
        return response


class LocalizationMessagesView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, locale):
        if locale not in SUPPORTED_LOCALES:
            return Response({"code": "unsupported_locale"}, status=404)
        return Response({"locale": locale, "catalog_delivery": "bundled", "version": os.getenv("APP_REVISION", "development")})


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class LeadSubmissionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "lead_submission"

    def post(self, request):
        serializer = LeadSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not idempotency_key or len(idempotency_key) > 200:
            return Response({"code": "idempotency_key_required", "message": "Please retry the form."}, status=status.HTTP_400_BAD_REQUEST)

        key_hash = _hash(idempotency_key)
        existing = LeadSubmission.objects.filter(idempotency_key_hash=key_hash).first()
        if existing:
            return Response({"request_id": str(existing.request_id), "status": existing.delivery_status}, status=status.HTTP_200_OK)

        fingerprint = _hash("|".join([
            data["work_email"].lower(), data["phone_number"], data["product_interest"].lower(),
        ]))
        duplicate = LeadSubmission.objects.filter(
            duplicate_fingerprint=fingerprint,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24),
        ).first()
        if duplicate:
            return Response({"code": "duplicate_lead", "message": "This request was already received.", "request_id": str(duplicate.request_id)}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            lead = serializer.save(idempotency_key_hash=key_hash, duplicate_fingerprint=fingerprint)
            transaction.on_commit(lambda: deliver_lead.delay(lead.pk))
        response = Response({"request_id": str(lead.request_id), "status": "queued"}, status=status.HTTP_202_ACCEPTED)
        response["X-Request-ID"] = str(lead.request_id)
        return response


class AnalyticsEventView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics_event"

    def post(self, request):
        serializer = AnalyticsEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response({"event_id": event.pk}, status=status.HTTP_202_ACCEPTED)


class AnalyticsEventBatchView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics_event"

    def post(self, request):
        events = request.data.get("events", []) if isinstance(request.data, dict) else []
        if not isinstance(events, list) or not 1 <= len(events) <= 50:
            return Response({"code": "invalid_batch", "message": "Submit between 1 and 50 events."}, status=400)
        serializer = AnalyticsEventSerializer(data=events, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"accepted": len(events)}, status=status.HTTP_202_ACCEPTED)


class PublicIndustriesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, industry=None):
        items = [{"code": code, "slug": item["slug"], "name": item["name"], "campaign": item["campaign"], "status": "available", "solutions": item["solutions"]} for code, item in INDUSTRIES.items()]
        if industry:
            match = next((item for item in items if item["slug"] == industry), None)
            return Response(match, status=200) if match else Response({"code": "not_found"}, status=404)
        return Response({"results": items})


class AvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"demo_requests": "available", "delivery_mode": "mock", "live_workflows": False})

class PublicIntegrationsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"results": [{"code": code, "status": status} for code, status in [("odoo", "staging_required"), ("n8n", "planned"), ("vicidial", "planned"), ("shopify", "planned"), ("calendar", "planned")]]})

class PublicScenariosView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, industry):
        item = next((v for v in INDUSTRIES.values() if v["slug"] == industry or industry in INDUSTRIES and v == INDUSTRIES[industry]), None)
        return Response({"industry": industry, "simulation": True, "scenarios": ["inquiry", "qualification", "human_handoff"]}) if item else Response({"code": "not_found"}, status=404)

class ConsentView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        if request.data.get("state") not in ("granted", "denied"):
            return Response({"code": "invalid_consent"}, status=400)
        return Response({"accepted": True, "policy_version": request.data.get("policy_version", "")}, status=202)

class RoiCalculationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            volume, missed, value, conversion = (max(0, float(request.data.get(k, 0))) for k in ("volume", "missed_percent", "lead_value", "conversion_percent"))
        except (TypeError, ValueError):
            return Response({"code": "invalid_calculation"}, status=400)
        missed_count = round(volume * min(missed, 100) / 100)
        monthly = round(missed_count * min(conversion, 100) / 100 * value, 2)
        return Response({"estimate": True, "missed_inquiries": missed_count, "monthly_opportunity": monthly, "annual_opportunity": monthly * 12})


class ServiceStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, check="live"):
        if check == "ready":
            LeadSubmission.objects.order_by("pk").values_list("pk", flat=True).first()
        return Response({"status": "ok", "check": check})


class ServiceManifestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"service": "codestra-industry-ai", "api_version": "v1", "delivery_mode": "mock", "live_integrations": False})


class MetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        geoip_path = Path(os.getenv("GEOIP_COUNTRY_DB", "/var/lib/geoip/GeoLite2-Country.mmdb"))
        return Response({
            "lead_submissions": LeadSubmission.objects.count(),
            "queued_leads": LeadSubmission.objects.filter(delivery_status="queued").count(),
            "failed_leads": LeadSubmission.objects.filter(delivery_status="failed").count(),
            "analytics_events": AnalyticsEvent.objects.count(),
            "dead_letter_leads": LeadSubmission.objects.filter(delivery_status="dead_letter").count(),
            "localization": {
                "supported_locales": len(SUPPORTED_LOCALES),
                "geoip_database_present": geoip_path.is_file(),
                "geoip_database_age_seconds": round(timezone.now().timestamp() - geoip_path.stat().st_mtime) if geoip_path.is_file() else None,
            },
        })


class PrometheusMetricsView(APIView):
    """Private scrape endpoint; proxy configuration must keep /internal/ private."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from django.db import connection
        from payment_app.models import StripeWebhookEvent, WebhookDelivery
        lines = [
            "# TYPE codestra_lead_submissions_total gauge",
            f"codestra_lead_submissions_total {LeadSubmission.objects.count()}",
            f"codestra_lead_queue_depth {LeadSubmission.objects.filter(delivery_status='queued').count()}",
            f"codestra_lead_dead_letter_total {LeadSubmission.objects.filter(delivery_status='dead_letter').count()}",
            f"codestra_webhook_deliveries_total {WebhookDelivery.objects.count()}",
            f"codestra_webhook_deliveries_failed {WebhookDelivery.objects.filter(status='failed').count()}",
            f"codestra_payment_webhook_events_total {StripeWebhookEvent.objects.count()}",
            "codestra_worker_heartbeat 1",
            f"codestra_database_up {1 if connection.is_usable() else 0}",
        ]
        return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4")
