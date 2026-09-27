# Webhook subscriptions and signing contract

## Authenticated management API

All management routes require the existing JWT bearer token and are scoped to
the authenticated user:

* `GET/POST /api/payment/subscriptions/`
* `GET/PATCH/DELETE /api/payment/subscriptions/{id}/`
* `POST /api/payment/subscriptions/{id}/test/`
* `GET /api/payment/deliveries/`

Creation accepts `name`, `url`, and one or more event names. Supported events
are `test`, `lead.created`, `delivery.updated`, `payment.succeeded`, and
`payment.failed`. A generated secret is returned once at creation; subsequent
responses expose only a four-character hint. PATCH can disable a subscription
without deleting its history.

## Delivery payload and signature

The receiver gets JSON in this shape:

```json
{
  "id": "delivery-event-uuid",
  "type": "test",
  "data": {"message": "Codestra webhook test", "staging": true}
}
```

Headers:

* `X-Codestra-Event-Id`: event UUID
* `X-Codestra-Signature`: `t=<unix-seconds>,v1=<hex-hmac-sha256>`
* `Content-Type: application/json`

The HMAC input is the exact request body prefixed with `<timestamp>.`, using
the subscription secret and SHA-256. Receivers should reject timestamps older
than five minutes and use constant-time comparison.

## Retry contract

2xx responses mark a delivery `delivered`. Timeouts, connection failures, and
5xx responses are retried up to three Celery attempts with backoff. Other 4xx
responses mark the delivery `failed`. Every attempt records status, attempt
count, response code, bounded response text, and a safe failure code.

## Staging receiver

`POST /api/payment/staging-receiver/` is available only when
`WEBHOOK_STAGING_MODE=true` and validates the same signature contract. It is
not enabled in production. End-to-end staging acceptance verified a controlled
unavailable receiver (five attempts), successful retry delivery with HTTP 202,
and tampered-signature rejection with HTTP 401.
