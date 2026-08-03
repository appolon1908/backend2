"""Envelope encryption for webhook signing secrets.

The master key is read only from a protected ``*_FILE`` path.  Ciphertext is
safe to persist; the key and plaintext secret never enter the database or API
responses.
"""
import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_VERSION = "v1"
NONCE_BYTES = 12


def _master_key() -> bytes:
    key_file = os.getenv("WEBHOOK_SECRET_KEY_FILE", "/run/secrets/codestra_webhook_secret_key")
    try:
        encoded = Path(key_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError("WEBHOOK_SECRET_KEY_FILE is unavailable") from exc
    try:
        key = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise RuntimeError("webhook master key must be base64") from exc
    if len(key) != 32:
        raise RuntimeError("webhook master key must decode to 32 bytes")
    return key


def fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def encrypt(secret: str, key_version: str = KEY_VERSION) -> tuple[str, str]:
    nonce = os.urandom(NONCE_BYTES)
    aad = f"codestra:webhook:{key_version}".encode("utf-8")
    ciphertext = AESGCM(_master_key()).encrypt(nonce, secret.encode("utf-8"), aad)
    return base64.urlsafe_b64encode(ciphertext).decode("ascii"), base64.urlsafe_b64encode(nonce).decode("ascii")


def decrypt(ciphertext: str, nonce: str, key_version: str = KEY_VERSION) -> str:
    aad = f"codestra:webhook:{key_version}".encode("utf-8")
    raw = AESGCM(_master_key()).decrypt(base64.urlsafe_b64decode(nonce), base64.urlsafe_b64decode(ciphertext), aad)
    return raw.decode("utf-8")
