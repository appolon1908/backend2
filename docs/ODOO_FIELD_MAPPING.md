# Odoo CRM field mapping

Standard mappings target `crm.lead`: `name`, `contact_name`, `partner_name`, `email_from`, `phone`, `description`, `type`, `team_id`, and `campaign_id`.

The following custom fields are intentionally centralized and must be confirmed or created before live activation: language, industry, monthly call volume, product interest, preferred demo time, consent, CTA source, UTM source/medium/campaign/term/content, `gclid`, and `fbclid`. Their proposed technical names are in `lead_capture/odoo_mapping.py`; no production schema is assumed.

Default mode is mock. A successful mock delivery proves the boundary and queue behavior, not live Odoo activation.
