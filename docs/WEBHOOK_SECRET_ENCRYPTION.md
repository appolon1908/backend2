# Webhook secret storage and rotation

`WebhookSubscription` stores AES-256-GCM ciphertext, a random 96-bit nonce,
key version, SHA-256 fingerprint, and bounded previous-secret overlap metadata.
The master key is loaded from `WEBHOOK_SECRET_KEY_FILE` (normally a mounted
Docker/Kubernetes secret) and is never read from the database, image, Git,
logs, metrics, or serializers. New and rotated secrets are returned once only.

Migration `0004_webhook_secret_envelope` adds the envelope columns. Migration
`0005_encrypt_legacy_webhook_secrets` encrypts any disposable legacy values and
removes the plaintext column. Migration `0006_webhook_audit_event` records
create/rotate/revoke actions without secret material.

Rotation is organization-admin/staff-only, keeps the previous key for 15
minutes, and records the overlap duration. Revocation disables delivery and
causes signing to fail closed. Production activation requires a protected key
file with mode 0600 (or the container secret equivalent) and a tested rotation
runbook.
