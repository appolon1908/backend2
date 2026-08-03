"""Private service boundary. The reverse proxy must not publish /internal/."""
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LeadSubmission
from .tasks import deliver_lead

class ServiceAuthenticatedView(APIView):
    authentication_classes = []
    permission_classes = []

    def dispatch(self, request, *args, **kwargs):
        secret = getattr(settings, "INTERNAL_SERVICE_SECRET", "")
        service, timestamp, signature = (request.headers.get(k, "") for k in ("X-Service-ID", "X-Timestamp", "X-Signature"))
        try: fresh = abs(time.time() - int(timestamp)) <= 300
        except ValueError: fresh = False
        digest = hmac.new(secret.encode(), timestamp.encode() + b"." + request.body, hashlib.sha256).hexdigest() if secret else ""
        replay = f"internal-signature:{signature}"
        if not secret or service not in getattr(settings, "INTERNAL_SERVICE_ALLOWLIST", []) or not fresh or not hmac.compare_digest(digest, signature) or cache.get(replay):
            return JsonResponse({"code": "service_authentication_failed"}, status=401)
        cache.set(replay, True, 300)
        return super().dispatch(request, *args, **kwargs)

class DeliveryView(ServiceAuthenticatedView):
    def get(self, request, submission_id):
        lead = LeadSubmission.objects.filter(request_id=submission_id).first()
        return Response({"submission_id": submission_id, "status": lead.delivery_status, "attempts": lead.delivery_attempts}) if lead else Response({"code": "not_found"}, status=404)
    def post(self, request):
        lead = LeadSubmission.objects.filter(request_id=request.data.get("submission_id")).first()
        if not lead: return Response({"code": "not_found"}, status=404)
        lead.delivery_status = LeadSubmission.DeliveryStatus.QUEUED; lead.save(update_fields=["delivery_status", "updated_at"]); deliver_lead.delay(lead.pk)
        return Response({"accepted": True, "submission_id": str(lead.request_id)}, status=202)

class ReconciliationView(ServiceAuthenticatedView):
    def get(self, request):
        failures = LeadSubmission.objects.filter(delivery_status__in=["failed", "dead_letter"]).order_by("created_at")[:100]
        return Response({"results": [{"submission_id": str(x.request_id), "status": x.delivery_status, "attempts": x.delivery_attempts} for x in failures]})
    def post(self, request):
        count = 0
        for lead in LeadSubmission.objects.filter(delivery_status__in=["failed", "dead_letter"])[:100]:
            lead.delivery_status = "queued"; lead.save(update_fields=["delivery_status", "updated_at"]); deliver_lead.delay(lead.pk); count += 1
        return Response({"accepted": count}, status=202)

class ControlledEventView(ServiceAuthenticatedView):
    def post(self, request):
        # Boundary exists for approved services; external execution remains disabled in mock mode.
        return Response({"accepted": True, "execution_mode": "mock", "event_id": hashlib.sha256(json.dumps(request.data, sort_keys=True).encode()).hexdigest()[:16]}, status=202)
