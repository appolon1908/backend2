# Codestra API contract audit — 2026-08-03

## Frontend callers reconciled

The React client uses the following backend contracts. Existing Django router
routes retain trailing slashes; the versioned lead/localization calls are
slashless because `APPEND_SLASH` is disabled and match the explicit paths.

| Client call | Method | Backend route | Result |
| --- | --- | --- | --- |
| `/api/auth/login/` | POST | `auth_app` router login | matched |
| `/api/auth/signup/` | POST | `auth_app` router signup | matched |
| `/api/cms/contact-us/` | POST | `cms` contact-us router | matched |
| `/api/cms/electronic-billing-interest/` | POST | `cms` electronic-billing-interest router | matched |
| `/api/cms/tax-payer/` | POST | `cms` tax-payer router | matched |
| `/api/cms/logo/` | GET | `cms` logo router | matched |
| `/api/cms/faqs/` | GET | `cms` faqs router | matched |
| `/api/cms/testimonial/` | GET | `cms` testimonial router | matched |
| `/api/employee/` | GET | `employee` router | matched |
| `/api/v1/leads` | POST | lead capture | matched |
| `/api/v1/demo-requests` | POST | lead capture | matched |
| `/api/v1/pricing-requests` | POST | lead capture | matched |
| `/api/v1/contact-requests` | POST | lead capture | matched |
| `/api/v1/analytics/events` | POST | analytics ingestion | matched |
| `/api/v1/localization/{config,country,preference}` | GET/POST | localization views | matched |

## Corrections

* Added canonical authenticated `POST /api/payment/stripe-payment/`.
* Retained `POST /api/payment/stipe-payment/` as a compatibility alias.
* Stripe webhook validation now rejects missing/invalid signatures, persists
  event receipts, rejects payload mutation, deduplicates processed events, and
  returns 5xx on processing failure so Stripe can retry.

## Staging evidence

The disposable staging stack used PostgreSQL 16, Redis 7.4, and the built
backend image. Health and localization returned 200; unauthenticated payment
creation returned 401; a correctly signed Stripe event returned 200, its
duplicate returned 200 without reprocessing, and an invalid signature returned
400. The stack and its network were removed after verification.
