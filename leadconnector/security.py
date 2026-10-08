"""HighLevel Marketplace Ed25519 signature verification over exact raw bytes.
Official key: https://marketplace.gohighlevel.com/docs/webhook/WebhookIntegrationGuide/
No legacy/unsigned workflow-webhook fallback is accepted.
"""
import base64
import binascii
from django.conf import settings
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg=\n-----END PUBLIC KEY-----\n"

def verify(body, signature):
    pem = getattr(settings, "LEADCONNECTOR_PUBLIC_KEY", PUBLIC_KEY)
    key = load_pem_public_key(pem.encode())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Configured key is not Ed25519")
    if not signature or len(signature) > 128:
        return False
    try:
        decoded = base64.b64decode(signature, validate=True)
        key.verify(decoded, body)
    except (InvalidSignature, ValueError, binascii.Error):
        return False
    return True
