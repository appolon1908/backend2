from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from . import security
from .models import ChatLead, WebhookReceipt
from .service import LOCATION, InvalidEvent, EventConflict, parse_event, ingest

class WebhookThrottle(AnonRateThrottle):
    rate = "120/min"

@csrf_exempt
@require_POST
def webhook(request):
    # Only this signed machine-to-machine route is CSRF-exempt.
    if not getattr(settings,"LEADCONNECTOR_ENABLED",False):
        return JsonResponse({"error":"integration_disabled"},status=503)
    if request.content_type != "application/json":
        return JsonResponse({"error":"json_required"},status=415)
    try:
        length = int(request.META.get("CONTENT_LENGTH") or 0)
        if length > 65536:
            return JsonResponse({"error":"payload_too_large"},status=413)
        body = request.body
    except (RequestDataTooBig,ValueError):
        return JsonResponse({"error":"payload_too_large"},status=413)
    if len(body) > 65536:
        return JsonResponse({"error":"payload_too_large"},status=413)
    throttle=WebhookThrottle()
    if not throttle.allow_request(request,None):
        return JsonResponse({"error":"rate_limited"},status=429,headers={"Retry-After":str(max(1,int(throttle.wait() or 60)))})
    try:
        verified=security.verify(body,request.headers.get("X-GHL-Signature",""))
    except (ValueError,TypeError,AttributeError):
        return JsonResponse({"error":"verification_unavailable"},status=503)
    if not verified:
        return JsonResponse({"error":"invalid_signature"},status=403)
    try:
        event = parse_event(body)
        if event["locationId"] != getattr(settings,"LEADCONNECTOR_LOCATION_ID",LOCATION):
            return JsonResponse({"error":"wrong_location"},status=403)
        result=ingest(event)
    except InvalidEvent:
        return JsonResponse({"error":"invalid_event"},status=400)
    except EventConflict:
        return JsonResponse({"error":"event_conflict"},status=409)
    return JsonResponse(result)

class CanViewChatLeads(permissions.BasePermission):
    def has_permission(self,request,view):
        return bool(request.user.is_authenticated and request.user.has_perm("leadconnector.view_chatlead"))

class LeadList(APIView):
    permission_classes=[CanViewChatLeads]
    def get(self,request):
        fields=("id","contact_id","widget_id","first_name","last_name","email","phone","last_message","sms_consent","allow_external_contact","created_at","updated_at")
        rows=ChatLead.objects.filter(location_id=getattr(settings,"LEADCONNECTOR_LOCATION_ID",LOCATION)).values(*fields)
        pager=PageNumberPagination(); pager.page_size=25
        return pager.get_paginated_response(pager.paginate_queryset(rows,request,view=self))

class IntegrationStatus(APIView):
    permission_classes=[CanViewChatLeads]
    def get(self,request):
        rows=WebhookReceipt.objects.filter(location_id=getattr(settings,"LEADCONNECTOR_LOCATION_ID",LOCATION))
        latest=rows.first()
        return Response({"enabled":getattr(settings,"LEADCONNECTOR_ENABLED",False),
                         "receipts":rows.count(),"last_received_at":latest.received_at if latest else None,
                         "outbound_contact_enabled":False,"carrier_approval":"not_verified"})
