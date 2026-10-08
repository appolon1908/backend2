"""Real PostgreSQL concurrency regression; SQLite cannot certify row locking."""
import base64
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.apps import apps
from django.db import connection, close_old_connections
from django.test import Client, TransactionTestCase, override_settings
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

@skipUnless(connection.vendor == "postgresql", "PostgreSQL required for concurrent row-lock certification")
class LeadConnectorConcurrencyTests(TransactionTestCase):
    def test_two_concurrent_deliveries_create_one_receipt_and_one_lead(self):
        key=Ed25519PrivateKey.generate()
        public=key.public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo).decode()
        body=json.dumps({"type":"InboundMessage","locationId":"jpzEheys0lV7R6jsD8W9",
            "chatWidgetId":"6ac7add4b17ff091c6b9a42c","contactId":"parallel-contact",
            "messageId":"parallel-message","webhookId":"parallel-event","body":"Synthetic concurrency test","direction":"inbound"}).encode()
        signature=base64.b64encode(key.sign(body)).decode()
        barrier=Barrier(2)
        def deliver(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                response=Client().post("/api/leadconnector/webhook/",body,content_type="application/json",HTTP_X_GHL_SIGNATURE=signature)
                return response.status_code
            finally:
                connection.close()
        with override_settings(LEADCONNECTOR_ENABLED=True,LEADCONNECTOR_PUBLIC_KEY=public):
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(list(pool.map(deliver,range(2))),[200,200])
        self.assertEqual(apps.get_model("leadconnector","WebhookReceipt").objects.count(),1)
        self.assertEqual(apps.get_model("leadconnector","ChatLead").objects.count(),1)
