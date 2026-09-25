# Codestra Industry AI Platform

## Architecture and controlled boundary

The React/Vite frontend renders `/industries` and 25 industry pages from one typed configuration system. Conversion pages preserve validated industry, solution, and CTA context. Django owns validation, authoritative campaign resolution, explainable scoring, duplicate suppression, idempotency, queue acceptance, first-party event ingestion, health, readiness, and protected metrics. Celery performs delivery through a mock or Odoo adapter. `LEAD_DELIVERY_MODE=mock` is the required default.

The browser never receives Odoo credentials, numeric campaign/team IDs, internal URLs, or workflow credentials. `/internal/v1/*` requires an allowlisted service ID, a five-minute timestamp, HMAC-SHA256 signature over `<timestamp>.<raw body>`, and replay protection. Caddy intentionally does not route `/internal/*` publicly.

## Routes and campaign map

| Route | Industry code | Authoritative campaign |
|---|---|---|
| `/industries` | `overview` | `INDUSTRY_AI_OVERVIEW` |
| `/industries/logistics-ai` | `logistics` | `LOGISTICS_AI` |
| `/industries/legal-ai` | `legal` | `LEGAL_AI` |
| `/industries/healthcare-ai` | `healthcare` | `HEALTHCARE_AI` |
| `/industries/senior-care-ai` | `senior_care` | `SENIOR_CARE_AI` |
| `/industries/real-estate-ai` | `real_estate` | `REAL_ESTATE_AI` |
| `/industries/financial-services-ai` | `financial_services` | `FINANCIAL_AI` |
| `/industries/ecommerce-ai` | `ecommerce` | `ECOMMERCE_AI` |
| `/industries/hospitality-ai` | `hospitality` | `HOSPITALITY_AI` |
| `/industries/construction-ai` | `construction` | `CONSTRUCTION_AI` |
| `/industries/agriculture-ai` | `agriculture` | `AGRICULTURE_AI` |
| `/industries/education-ai` | `education` | `EDUCATION_AI` |
| `/industries/dental-ai` | `dental` | `DENTAL_AI` |
| `/industries/veterinary-ai` | `veterinary` | `VETERINARY_AI` |
| `/industries/automotive-ai` | `automotive` | `AUTOMOTIVE_AI` |
| `/industries/restaurant-ai` | `restaurant` | `RESTAURANT_AI` |
| `/industries/manufacturing-ai` | `manufacturing` | `MANUFACTURING_AI` |
| `/industries/recruitment-ai` | `recruitment` | `RECRUITMENT_AI` |
| `/industries/nonprofit-ai` | `nonprofit` | `NONPROFIT_AI` |
| `/industries/public-services-ai` | `public_services` | `PUBLIC_SERVICES_AI` |
| `/industries/energy-ai` | `energy` | `ENERGY_AI` |
| `/industries/telecom-it-ai` | `telecom_it` | `TELECOM_IT_AI` |
| `/industries/wellness-ai` | `wellness` | `WELLNESS_AI` |
| `/industries/security-services-ai` | `security_services` | `SECURITY_SERVICES_AI` |
| `/industries/marketing-media-ai` | `marketing_media` | `MARKETING_MEDIA_AI` |
| `/industries/gaming-entertainment-ai` | `gaming_entertainment` | `GAMING_ENTERTAINMENT_AI` |

Conversion routes are `/book-demo`, `/request-pricing`, `/contact`, `/thank-you`, `/security`, `/privacy`, and `/terms`. Query context is allowlisted; campaign IDs are never accepted from it.

## CTA map

`request_demo` → `/book-demo`; `call_codestra` → configured `tel:` only; `view_workflow` → local workflow; `project_consultation` → `/contact`; `request_pricing` → `/request-pricing`; `audio_demo` → local simulation; `roi_calculator` → calculator; `view_integrations` → integrations; `cross_industry` → a configured industry route. Events record label, code, position, section, industry, solution, session, language, device, consent, and attribution—never lead content.

## Lead, scoring, routing, and SLA

The canonical public contract remains compatible with the deployed form and accepts an optional allowlisted `solution`. The backend normalizes phone numbers; enforces consent and honeypot; hashes idempotency keys; suppresses a 24-hour email/phone/solution duplicate; and assigns `industry_code`, `campaign_code`, `solution_code`, `lead_score`, `lead_classification`, and `follow_up_sla_minutes`.

Auditable scoring: valid business email 15; valid phone 15; company size above 10 employees 10; stated volume 10; clear requirement 15; high-intent canonical CTA 20; preferred date 15. Classification: 0–29 nurture, 30–59 MQL, 60–79 SQL, 80–100 priority opportunity. No sensitive or protected characteristic is used.

Configurable follow-up targets are 5 minutes for call request, 15 for demo, 30 for pricing, 120 for consultation, and one business day otherwise. These are internal targets and are not public promises. Country, language, size, volume, capacity, owner, and numeric team routing remain configuration/readiness work before activation.

## Odoo field readiness

Standard candidates: `contact_name`, `partner_name`, `email_from`, `phone`, `name`, `description`, `campaign_id`, `source_id`, `medium_id`, `team_id`, `user_id`, `type`. Custom mappings for industry, solution, size, volume, language, systems, preferred time, CTA/context, first/last attribution, click IDs, consent, score, submission ID, and delivery status must be confirmed against the real schema. Numeric records are resolved server-side through `ODOO_ROUTING_MAP`; each campaign entry must contain confirmed `campaign_id`, `team_id`, `source_id`, and `medium_id`. Production delivery fails closed when a route is absent. No custom field name is assumed.

Live activation requires schema inspection, campaign/source/medium/team confirmation, least-privilege access, staging delivery, duplicate proof, activity creation proof, rollback proof, and explicit authorization. This build does not authorize live writes.

## Reliability and reconciliation

Valid submissions return success only after the database transaction durably accepts them and schedules queue delivery. Celery uses exponential backoff, jitter, a five-retry maximum, bounded Odoo timeout, and dead-letter status. Operators inspect protected metrics or signed `/internal/v1/odoo/reconciliation/failures`, replay one submission through `/internal/v1/odoo/delivery/retry`, or replay a bounded failure batch through `/internal/v1/odoo/reconciliation/run`. Correlate by submission ID; never place PII in logs or metric labels.

Rollback: switch `LEAD_DELIVERY_MODE=mock`, stop workers if unsafe execution is suspected, preserve queued records, deploy the prior immutable image, run migrations only when compatible, verify `/health/live` and `/health/ready`, then reconcile after root cause approval.

## Consent, privacy, and retention

Privacy consent is required; marketing consent is independent. Store policy version and timestamp when the extended contract is enabled. First- and last-touch attribution are retained with the lead. Analytics rejects unapproved event names and strips attribution keys outside the UTM/click allowlist. Never send medical details, legal narratives, financial data, documents, transcripts, names, email, or full phone numbers to analytics. Production retention periods require owner/legal approval; implement scheduled deletion/anonymization before live sensitive workflows.

## Monitoring, dashboards, and alerts

Public probes: `/health/live`, `/health/ready`, and `/.well-known/codestra-service`. `/metrics` requires staff authentication/network restriction. Metrics cover accepted/queued/failed/dead-letter submissions and analytics volume without personal labels.

Dashboards: website health (availability, latency, errors, Web Vitals, broken links); lead delivery (accepted, success, latency, retries, duplicates, queue/dead letter); marketing (visits, CTA/form/MQL/demo/opportunity funnel by approved dimensions); Odoo (campaign/team completeness, activities, SLA, stages, outcomes).

Recommended configurable alerts: availability failures; API 5xx >2%/5m; delivery failures >5%/15m; oldest queue >15m; any dead letter; analytics failures >2%/15m; bot submissions >3× baseline; conversion decrease >40% against sufficient baseline; missing campaign/team/activity; expiring credentials. Alerts contain counts and service context only.

## Deployment and activation checklist

1. Build immutable frontend/backend images; scan dependencies and secrets.
2. Back up database; apply migrations in staging; run Django checks/tests.
3. Run frontend format/lint/type/build and Playwright at required viewports/browsers.
4. Deploy with `LEAD_DELIVERY_MODE=mock`; migrate; verify probes, protected metrics, sitemap, every route/CTA/form.
5. Exercise acceptance, duplicate, retry, dead-letter, replay, and reconciliation paths.
6. For Odoo staging only, confirm mapping and credentials, set the staging adapter, test each campaign/team/activity, and restore mock mode.
7. Obtain explicit live-write authorization before one canary; monitor and retain rollback readiness.

Environment variables are documented in `.env.example`; live values belong in a secret manager and must never be committed.
