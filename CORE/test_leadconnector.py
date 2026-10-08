"""Synthetic-only, signed webhook contract tests. No provider is contacted."""
import base64
import json
from datetime import timedelta
from django.apps import apps
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ENDPOINT = "/api/leadconnector/webhook/"
LOCATION = "jpzEheys0lV7R6jsD8W9"
WIDGET = "6ac7add4b17ff091c6b9a42c"

class LeadConnectorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_key = Ed25519PrivateKey.generate()
        self.settings_override = override_settings(
            LEADCONNECTOR_ENABLED=True,
            LEADCONNECTOR_PUBLIC_KEY=self.private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode(),
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.event = {"type":"InboundMessage", "locationId":LOCATION, "chatWidgetId":WIDGET,
            "contactId":"synthetic-contact", "messageId":"synthetic-message", "webhookId":"synthetic-event",
            "direction":"inbound", "messageType":"Live_Chat", "body":"Synthetic enquiry only",
            "from":"+12025550123", "timestamp":timezone.now().isoformat()}

    def send(self, event=None, raw=None, signature=None):
        body = raw if raw is not None else json.dumps(self.event if event is None else event).encode()
        signed = signature if signature is not None else base64.b64encode(self.private_key.sign(body)).decode()
        return self.client.post(ENDPOINT, data=body, content_type="application/json", HTTP_X_GHL_SIGNATURE=signed)

    def model(self, name):
        return apps.get_model("leadconnector", name)

    def test_verified_message_creates_local_review_lead(self):
        response = self.send()
        self.assertEqual(response.status_code, 200)
        lead = self.model("ChatLead").objects.get()
        self.assertEqual(lead.contact_id, "synthetic-contact")
        self.assertEqual(lead.last_message, "Synthetic enquiry only")
        self.assertEqual(lead.phone, "+12025550123")
        self.assertEqual(lead.sms_consent, "unknown")
        self.assertFalse(lead.allow_external_contact)

    def test_duplicate_is_idempotent(self):
        self.assertEqual(self.send().status_code, 200)
        response = self.send()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["duplicate"])
        self.assertEqual(self.model("WebhookReceipt").objects.count(), 1)
        self.assertEqual(self.model("ChatLead").objects.count(), 1)

    def test_same_event_id_different_body_is_conflict(self):
        self.assertEqual(self.send().status_code, 200)
        response = self.send({**self.event, "body":"changed"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.model("ChatLead").objects.get().last_message, "Synthetic enquiry only")

    def test_signed_body_is_verified_before_parsing(self):
        response = self.send(raw=b"not json", signature="invalid")
        self.assertEqual(response.status_code, 403)

    def test_missing_signature_and_legacy_header_rejected(self):
        response = self.client.post(ENDPOINT, json.dumps(self.event), content_type="application/json", HTTP_X_WH_SIGNATURE="legacy")
        self.assertEqual(response.status_code, 403)

    def test_tampered_signature_rejected(self):
        signature = base64.b64encode(self.private_key.sign(b"different bytes")).decode()
        self.assertEqual(self.send(signature=signature).status_code, 403)

    def test_wrong_location_rejected(self):
        self.assertEqual(self.send({**self.event, "locationId":"foreign-location"}).status_code, 403)

    def test_different_widget_ignored_without_lead(self):
        response = self.send({**self.event, "chatWidgetId":"different-widget"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ignored")
        self.assertFalse(self.model("ChatLead").objects.exists())

    def test_absent_widget_does_not_import_unrelated_messages(self):
        event = dict(self.event); event.pop("chatWidgetId")
        response = self.send(event)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.model("ChatLead").objects.exists())

    def test_invalid_signed_json_and_duplicate_fields_rejected(self):
        for body in (b"[]", b"null", b"not json", b'{"type":"x","type":"y"}'):
            with self.subTest(body=body):
                self.assertEqual(self.send(raw=body).status_code, 400)

    def test_oversized_body_rejected(self):
        self.assertEqual(self.send(raw=b"x" * 65537).status_code, 413)

    def test_invalid_field_types_rejected(self):
        for field in ("contactId", "body", "locationId"):
            with self.subTest(field=field):
                self.assertEqual(self.send({**self.event, field:[]}).status_code, 400)

    def test_stale_and_future_signed_timestamps_rejected(self):
        for delta in (timedelta(days=-8), timedelta(hours=1)):
            self.assertEqual(self.send({**self.event, "timestamp":(timezone.now()+delta).isoformat()}).status_code, 400)

    def test_documented_payload_without_delivery_ids_deduplicates(self):
        event = dict(self.event)
        for field in ("timestamp", "webhookId", "messageId"):
            event.pop(field)
        self.assertEqual(self.send(event).status_code, 200)
        self.assertTrue(self.send(event).json()["duplicate"])

    def test_claimed_consent_does_not_grant_permission(self):
        event = {**self.event, "consent":True, "smsConsent":True, "dnd":False}
        self.assertEqual(self.send(event).status_code, 200)
        self.assertEqual(self.model("ChatLead").objects.get().sms_consent, "unknown")
        self.assertFalse(self.model("ChatLead").objects.get().allow_external_contact)

    def test_contact_update_only_enriches_existing_widget_lead(self):
        self.assertEqual(self.send().status_code, 200)
        event = {"type":"ContactUpdate", "locationId":LOCATION, "id":"synthetic-contact",
                 "webhookId":"contact-update", "firstName":"Synthetic", "lastName":"Test", "email":"test@example.invalid", "dnd":True}
        self.assertEqual(self.send(event).status_code, 200)
        lead=self.model("ChatLead").objects.get()
        self.assertEqual(lead.email, "test@example.invalid")
        self.assertEqual(lead.sms_consent, "withdrawn")
        self.assertFalse(lead.allow_external_contact)

    def test_unrelated_contact_is_not_imported(self):
        response=self.send({"type":"ContactCreate", "locationId":LOCATION, "id":"another-contact", "email":"unrelated@example.invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.model("ChatLead").objects.exists())

    def test_disabled_endpoint_is_fail_closed(self):
        with override_settings(LEADCONNECTOR_ENABLED=False):
            self.assertEqual(self.send().status_code, 503)

    def test_webhook_is_post_only(self):
        self.assertEqual(self.client.get(ENDPOINT).status_code, 405)

    def test_public_cannot_read_leads_or_receipts(self):
        for path in ("/api/leadconnector/leads/", "/api/leadconnector/status/"):
            self.assertIn(self.client.get(path).status_code, (401,403))

    def test_repeated_legacy_profile_updates_are_not_frozen(self):
        self.assertEqual(self.send().status_code,200)
        base={"type":"ContactUpdate","locationId":LOCATION,"id":"synthetic-contact"}
        self.assertEqual(self.send({**base,"webhookId":"profile1","firstName":"First"}).status_code,200)
        self.assertEqual(self.send({**base,"webhookId":"profile2","firstName":"Second"}).status_code,200)
        self.assertEqual(self.model("ChatLead").objects.get().first_name,"Second")

    def test_plain_legacy_messages_without_timestamps_are_not_frozen(self):
        event=dict(self.event)
        event.pop("timestamp")
        self.assertEqual(self.send(event).status_code,200)
        event.update(webhookId="new-event",messageId="new-message",body="Second message")
        self.assertEqual(self.send(event).status_code,200)
        self.assertEqual(self.model("ChatLead").objects.get().last_message,"Second message")

    def test_clearing_dnd_does_not_restore_consent(self):
        self.assertEqual(self.send({**self.event,"dnd":True}).status_code,200)
        response=self.send({"type":"ContactDndUpdate","locationId":LOCATION,"id":"synthetic-contact","webhookId":"dnd-off","dnd":False})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.model("ChatLead").objects.get().sms_consent,"withdrawn")

    def test_invalid_event_rolls_back_receipt_and_projection(self):
        response=self.send({**self.event,"dnd":"false"})
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.model("WebhookReceipt").objects.count(),0)
        self.assertEqual(self.model("ChatLead").objects.count(),0)

    def test_privileged_readback_is_location_scoped(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from django.contrib.auth.models import Permission
        self.assertEqual(self.send().status_code,200)
        user=get_user_model().objects.create_user(email="reviewer@example.invalid",password="test-password-only")
        client=APIClient();client.force_authenticate(user=user)
        self.assertEqual(client.get("/api/leadconnector/leads/").status_code,403)
        user.user_permissions.add(Permission.objects.get(codename="view_chatlead",content_type__app_label="leadconnector"))
        user=get_user_model().objects.get(pk=user.pk);client.force_authenticate(user=user)
        self.model("ChatLead").objects.create(location_id="foreign",contact_id="foreign",widget_id="foreign")
        response=client.get("/api/leadconnector/leads/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["count"],1)
        self.assertEqual(client.get("/api/leadconnector/status/").status_code,200)

    def test_sms_channel_dnd_blocks_contact_even_when_global_dnd_false(self):
        self.assertEqual(self.send().status_code,200)
        event={"type":"ContactDndUpdate","locationId":LOCATION,"id":"synthetic-contact","webhookId":"sms-dnd",
               "dnd":False,"dndSettings":{"SMS":{"status":"active"}}}
        self.assertEqual(self.send(event).status_code,200)
        self.assertEqual(self.model("ChatLead").objects.get().sms_consent,"withdrawn")

    def test_older_message_does_not_overwrite_newer_message(self):
        self.assertEqual(self.send().status_code,200)
        event={**self.event,"webhookId":"old-event","messageId":"old-message","body":"Earlier message",
               "timestamp":(timezone.now()-timedelta(hours=1)).isoformat()}
        self.assertEqual(self.send(event).status_code,200)
        self.assertEqual(self.model("ChatLead").objects.get().last_message,"Synthetic enquiry only")
