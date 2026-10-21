"""Local review records only. These models cannot authorize outbound contact."""
import uuid
from django.db import models

class ChatLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location_id = models.CharField(max_length=128)
    contact_id = models.CharField(max_length=128)
    widget_id = models.CharField(max_length=128)
    first_name = models.CharField(max_length=256, blank=True)
    last_name = models.CharField(max_length=256, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    profile_updated_at = models.DateTimeField(null=True, blank=True)
    sms_consent = models.CharField(max_length=16, default="unknown", choices=[("unknown","Unknown"),("withdrawn","Withdrawn")])
    allow_external_contact = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location_id","contact_id"], name="lc_unique_contact_location")]
        ordering = ["-updated_at","id"]

class WebhookReceipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location_id = models.CharField(max_length=128)
    event_key = models.CharField(max_length=256)
    body_sha256 = models.CharField(max_length=64)
    event_type = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default="received")
    consent_evidence = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location_id","event_key"], name="lc_unique_event_location")]
        ordering = ["-received_at","id"]
