# AI Receptionist API

## `POST /api/v1/leads`

Accepts the typed landing-page lead payload. Send an opaque `Idempotency-Key` header. Consent must be `true`; phone numbers are normalized; a hidden `honeypot` value causes rejection; matching email/phone/product submissions are deduplicated for 24 hours. Successful requests return `202 queued`; duplicates return `409`; throttling returns `429`. Logs contain request IDs and delivery state, not submitted personal data.

Delivery defaults to `LEAD_DELIVERY_MODE=mock`. Production mode is fail-closed unless Odoo credentials and `ODOO_FIELD_MAPPING_CONFIRMED=true` are present. Celery provides bounded retries and failed-delivery reconciliation through the Django admin retry action.

The same validated conversion contract is available at `/api/v1/demo-requests`, `/api/v1/pricing-requests`, and `/api/v1/contact-requests`. These routes preserve intent while sharing validation, consent, honeypot, idempotency, duplicate protection, throttling, queueing, and reconciliation behavior.

Public discovery endpoints: `/api/v1/public/industries`, `/api/v1/public/industries/:industry`, and `/api/v1/public/availability`.

Operational endpoints: `/health/live`, `/health/ready`, `/.well-known/codestra-service`, and staff-protected `/metrics`.

## `POST /api/v1/analytics/events`

Accepts allow-listed first-party events and non-identifying context. The endpoint rejects PII-shaped fields. The browser only sends events after analytics consent.

## Activation

1. Confirm the mappings in `lead_capture/odoo_mapping.py` against staging.
2. Set the documented Odoo environment variables in the secret store—not in Git.
3. Test create, duplicate, timeout, retry, reconciliation, and rollback flows in staging.
4. Obtain explicit production-write approval, then set production delivery mode.
