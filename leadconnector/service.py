"""Atomic, idempotent local projection. No email, SMS, call, or CRM dispatch."""
import hashlib
import json
import re
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import ChatLead, WebhookReceipt

LOCATION = "jpzEheys0lV7R6jsD8W9"
WIDGET = "6ac7add4b17ff091c6b9a42c"

class InvalidEvent(ValueError):
    pass

class EventConflict(ValueError):
    pass

def text(event, field, limit=128, required=False):
    value = event.get(field, "")
    if value is None and not required:
        return ""
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise InvalidEvent("Invalid " + field)
    return value

def identifier(event, field, required=False):
    value = text(event, field, required=required)
    if value and not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise InvalidEvent("Invalid " + field)
    return value

def event_time(event):
    # Delivery timestamp is optional in documented older payloads. Never use
    # an old contact creation date as a delivery freshness assertion.
    value = text(event, "timestamp", 64)
    if not value:
        return None
    try:
        parsed = parse_datetime(value)
    except ValueError as exc:
        raise InvalidEvent("Invalid timestamp") from exc
    if not parsed or timezone.is_naive(parsed):
        raise InvalidEvent("Invalid timestamp")
    now = timezone.now()
    if parsed < now-timedelta(days=7) or parsed > now+timedelta(minutes=5):
        raise InvalidEvent("Expired or future event")
    return parsed

def reject_duplicate_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvent("Duplicate JSON field")
        result[key] = value
    return result

def parse_event(body):
    try:
        event = json.loads(body, object_pairs_hook=reject_duplicate_fields,
                           parse_constant=lambda _: (_ for _ in ()).throw(InvalidEvent("Non-finite JSON")))
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise InvalidEvent("Invalid JSON object") from exc
    if not isinstance(event, dict):
        raise InvalidEvent("JSON object required")
    identifier(event, "locationId", required=True)
    text(event, "type", 64, required=True)
    return event

def sms_withdrawn(event):
    if "dnd" in event and not isinstance(event["dnd"], bool):
        raise InvalidEvent("Invalid dnd")
    settings = event.get("dndSettings", {})
    if not isinstance(settings, dict):
        raise InvalidEvent("Invalid dndSettings")
    sms = settings.get("SMS", {})
    if not isinstance(sms, dict):
        raise InvalidEvent("Invalid SMS dndSettings")
    status = text(sms, "status", 16)
    if status not in ("", "active", "inactive"):
        raise InvalidEvent("Invalid SMS DND status")
    return event.get("dnd") is True or status == "active"

def ingest(event):
    location = event["locationId"]
    kind = event["type"]
    canonical = json.dumps(event, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    delivery = identifier(event, "webhookId")
    message_id = identifier(event, "messageId") if kind == "InboundMessage" else ""
    event_key = "webhook:"+delivery if delivery else ("message:"+message_id if message_id else "body:"+digest)
    with transaction.atomic():
        prior = WebhookReceipt.objects.filter(location_id=location, event_key=event_key).first()
        if prior:
            if prior.body_sha256 != digest:
                raise EventConflict("Event ID reused with a different body")
            return {"status":prior.status, "duplicate":True}
        timestamp = event_time(event)
        receipt, created = WebhookReceipt.objects.get_or_create(
            location_id=location, event_key=event_key,
            defaults={"body_sha256":digest,"event_type":kind})
        if not created:
            if receipt.body_sha256 != digest:
                raise EventConflict("Event ID reused with a different body")
            return {"status":receipt.status,"duplicate":True}
        status = "ignored"
        lead = None
        widget = getattr(settings, "LEADCONNECTOR_WIDGET_ID", WIDGET)
        if kind == "InboundMessage" and text(event,"chatWidgetId") == widget:
            contact = identifier(event,"contactId",required=True)
            body = text(event,"body",10000,required=True)
            direction = text(event,"direction",16)
            if direction != "inbound":
                raise InvalidEvent("Inbound direction required")
            phone = text(event,"from",320)
            if phone and not re.fullmatch(r"\+[1-9][0-9]{7,14}",phone):
                phone = ""  # Never put email addresses or provider IDs in phone.
            lead, _ = ChatLead.objects.get_or_create(location_id=location,contact_id=contact,defaults={"widget_id":widget})
            lead = ChatLead.objects.select_for_update().get(pk=lead.pk)
            message_time = timestamp
            if not message_time:
                value = text(event,"dateAdded",64)
                try:
                    message_time = parse_datetime(value) if value else None
                except ValueError as exc:
                    raise InvalidEvent("Invalid dateAdded") from exc
                if value and (not message_time or timezone.is_naive(message_time)):
                    raise InvalidEvent("Invalid dateAdded")
            # Old payloads without an event clock use receipt order. Permanent
            # event deduplication still prevents replay; chronology cannot be
            # reconstructed when the provider omits timestamps entirely.
            message_time = message_time or timezone.now()
            if not lead.last_message_at or message_time >= lead.last_message_at:
                lead.last_message = body
                lead.last_message_at = message_time or timezone.now()
                if phone:
                    lead.phone = phone
                status = "processed"
            else:
                status = "stale"
        elif kind in {"ContactCreate","ContactUpdate","ContactDndUpdate"}:
            contact = identifier(event,"id",required=True)
            lead = ChatLead.objects.select_for_update().filter(location_id=location,contact_id=contact).first()
            if lead:
                # ContactCreate usually arrives before the first chat message.
                # It is ignored rather than importing unrelated location contacts.
                profile_time = timestamp or timezone.now()
                if not lead.profile_updated_at or profile_time >= lead.profile_updated_at:
                    for source,target,limit in (("firstName","first_name",256),("lastName","last_name",256),("phone","phone",32),("email","email",254)):
                        if source in event:
                            value=text(event,source,limit)
                            if source == "email" and value:
                                try: validate_email(value)
                                except ValidationError as exc: raise InvalidEvent("Invalid email") from exc
                            if source == "phone" and value and not re.fullmatch(r"\+[1-9][0-9]{7,14}",value):
                                raise InvalidEvent("Invalid phone")
                            setattr(lead,target,value)
                    lead.profile_updated_at = profile_time
                    status = "processed"
                else:
                    status = "stale"
        withdrawn = sms_withdrawn(event)
        if lead:
            # A withdrawal is sticky; dnd=false is NOT opt-in evidence.
            if withdrawn:
                lead.sms_consent = "withdrawn"
            lead.allow_external_contact = False
            lead.save()
        receipt.status = status
        receipt.consent_evidence = {
            "status":lead.sms_consent if lead else "unknown",
            "basis":"signed_dnd" if withdrawn else "no_verified_opt_in_evidence",
            "signature_verified":True,
            "provider_activity_review_required":True,
        }
        receipt.save(update_fields=["status","consent_evidence"])
        return {"status":status,"duplicate":False}
