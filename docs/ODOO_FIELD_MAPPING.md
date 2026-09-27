# Odoo CRM field mapping

Standard mappings target `crm.lead`: `name`, `contact_name`, `partner_name`, `email_from`, `phone`, `description`, `type`, `team_id`, and `campaign_id`.

The following custom fields are intentionally centralized and must be confirmed or created before live activation: language, industry, monthly call volume, product interest, preferred demo time, consent, CTA source, UTM source/medium/campaign/term/content, `gclid`, and `fbclid`. Their proposed technical names are in `lead_capture/odoo_mapping.py`; no production schema is assumed.

Default mode is mock. A successful mock delivery proves the boundary and queue behavior, not live Odoo activation.

## Lead submission endpoint

Visitor applications use `POST /api/v1/leads` (the demo, pricing, and contact
routes share the same validated contract). The endpoint stores the submission,
resolves campaign/team/source/medium server-side, and queues delivery. With
`LEAD_DELIVERY_MODE=production`, the worker sends a new `crm.lead` through the
configured Odoo middleware endpoint:

`POST {ODOO_BASE_URL}/api/v1/models/{ODOO_LEAD_MODEL}`

The request includes an idempotency key derived from the submission UUID and
the mapped `values`, `team_id`, `campaign_id`, `source_id`, `medium_id`, and
optional `user_id`. The internal retry endpoint is:

`POST /internal/v1/odoo/leads`

It requires the existing signed service headers and accepts a stored
`submission_id`; it never accepts arbitrary Odoo record IDs or browser-side
credentials.

Activation checklist: confirm the Odoo schema and routing records, set
`ODOO_FIELD_MAPPING_CONFIRMED=true`, provide credentials through protected
secret storage, set `LEAD_DELIVERY_MODE=production` in staging, verify the
created `crm.lead` and duplicate behavior, then obtain explicit approval before
changing production mode.
