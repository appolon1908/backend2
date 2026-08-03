import hashlib
import hmac
import json
import time
import uuid
from datetime import timedelta

from django.conf import settings
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from django.utils import timezone
from rest_framework.response import Response

from .models import WebhookAuditEvent, WebhookDelivery, WebhookSubscription
from .secret_crypto import encrypt, fingerprint
from .url_security import validate_webhook_url
from .webhook_delivery import deliver_webhook


EVENTS = {"payment.succeeded", "payment.failed", "lead.created", "delivery.updated", "test"}


class SubscriptionSerializer(serializers.ModelSerializer):
    secret = serializers.CharField(write_only=True, required=False)
    secret_hint = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WebhookSubscription
        fields = ("id", "name", "url", "events", "enabled", "secret", "secret_hint", "created_at", "updated_at")
        read_only_fields = ("id", "secret_hint", "created_at", "updated_at")

    def validate_events(self, value):
        if not isinstance(value, list) or not value or any(item not in EVENTS for item in value):
            raise serializers.ValidationError("Choose one or more supported events.")
        return value

    def validate_url(self, value):
        validate_webhook_url(value, allow_local=getattr(settings, "WEBHOOK_STAGING_MODE", False))
        return value

    def create(self, validated_data):
        secret = validated_data.pop("secret", None) or uuid.uuid4().hex + uuid.uuid4().hex
        ciphertext, nonce = encrypt(secret)
        instance = WebhookSubscription.objects.create(
            owner=self.context["request"].user,
            secret_ciphertext=ciphertext,
            secret_nonce=nonce,
            secret_fingerprint=fingerprint(secret),
            **validated_data,
        )
        instance._new_secret = secret
        WebhookAuditEvent.objects.create(subscription=instance, actor=self.context["request"].user, action="created")
        return instance

    def update(self, instance, validated_data):
        validated_data.pop("secret", None)
        return super().update(instance, validated_data)

    def get_secret_hint(self, obj):
        return f"••••{obj.secret_fingerprint[-4:]}"


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = ("id", "event_id", "event_type", "status", "attempts", "attempt_history", "response_code", "response_body", "error", "created_at", "delivered_at", "updated_at")


class WebhookSubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return WebhookSubscription.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response = Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
        response.data["secret"] = getattr(instance, "_new_secret", None)
        return response

    def get_throttles(self):
        if getattr(self, "action", None) == "send_test":
            self.throttle_scope = "webhook_test"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    @action(detail=True, methods=["post"], url_path="test")
    def send_test(self, request, pk=None):
        subscription = self.get_object()
        delivery = WebhookDelivery.objects.create(subscription=subscription, event_type="test", payload={"message": "Codestra webhook test", "staging": settings.DEBUG or getattr(settings, "WEBHOOK_STAGING_MODE", False)})
        deliver_webhook.delay(str(delivery.pk))
        return Response({"delivery_id": delivery.id, "status": "queued"}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"], url_path="rotate-secret", permission_classes=[IsAdminUser])
    def rotate_secret(self, request, pk=None):
        subscription = self.get_object()
        secret = uuid.uuid4().hex + uuid.uuid4().hex
        ciphertext, nonce = encrypt(secret)
        subscription.previous_secret_ciphertext = subscription.secret_ciphertext
        subscription.previous_secret_nonce = subscription.secret_nonce
        subscription.previous_secret_key_version = subscription.secret_key_version
        subscription.previous_secret_expires_at = timezone.now() + timedelta(minutes=15)
        subscription.secret_ciphertext = ciphertext
        subscription.secret_nonce = nonce
        subscription.secret_fingerprint = fingerprint(secret)
        subscription.secret_rotated_at = timezone.now()
        subscription.secret_revoked_at = None
        subscription.save()
        WebhookAuditEvent.objects.create(subscription=subscription, actor=request.user, action="rotated", metadata={"overlap_seconds": 900})
        return Response({"secret": secret, "secret_hint": f"••••{subscription.secret_fingerprint[-4:]}"})

    @action(detail=True, methods=["post"], url_path="revoke-secret", permission_classes=[IsAdminUser])
    def revoke_secret(self, request, pk=None):
        subscription = self.get_object()
        subscription.secret_revoked_at = timezone.now()
        subscription.enabled = False
        subscription.save(update_fields=["secret_revoked_at", "enabled", "updated_at"])
        WebhookAuditEvent.objects.create(subscription=subscription, actor=request.user, action="revoked")
        return Response({"status": "revoked"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def deliveries(request):
    results = WebhookDelivery.objects.filter(subscription__owner=request.user)[:100]
    return Response(DeliverySerializer(results, many=True).data)


def _valid_signature(secret, header, body):
    try:
        values = dict(item.split("=", 1) for item in header.split(","))
        timestamp = int(values["t"])
        if abs(time.time() - timestamp) > 300:
            return False
        expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, values["v1"])
    except (KeyError, ValueError):
        return False


@api_view(["POST"])
@permission_classes([AllowAny])
def staging_receiver(request):
    if not getattr(settings, "WEBHOOK_STAGING_MODE", False):
        return Response({"code": "staging_receiver_disabled"}, status=404)
    if len(request.body) > getattr(settings, "WEBHOOK_MAX_BODY_BYTES", 262144):
        return Response({"code": "payload_too_large"}, status=413)
    secret = getattr(settings, "WEBHOOK_STAGING_SECRET", "")
    if not secret or not _valid_signature(secret, request.headers.get("X-Codestra-Signature", ""), request.body):
        return Response({"code": "invalid_signature"}, status=401)
    if request.headers.get("X-Staging-Receiver-Mode") == "fail-once":
        key = hashlib.sha256(request.body).hexdigest()
        if not getattr(staging_receiver, "seen", set()).__contains__(key):
            staging_receiver.seen = getattr(staging_receiver, "seen", set()) | {key}
            return Response({"code": "controlled_failure"}, status=503)
    return Response({"accepted": True, "event_id": request.headers.get("X-Codestra-Event-Id")}, status=202)
