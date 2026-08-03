"""Central Odoo mapping. Custom field names require written confirmation before live mode."""

STANDARD_FIELDS = {
    "name": "lead_title",
    "contact_name": "full_name",
    "partner_name": "business_name",
    "email_from": "work_email",
    "phone": "phone_number",
    "description": "description",
    "type": "lead_type",
}

CUSTOM_FIELDS_TO_CONFIRM = {
    "x_codestra_language": "preferred_language",
    "x_codestra_industry": "industry",
    "x_codestra_monthly_call_volume": "monthly_call_volume",
    "x_codestra_product_interest": "product_interest",
    "x_codestra_preferred_demo_time": "preferred_demo_time",
    "x_codestra_consent": "consent",
    "x_codestra_cta_source": "cta_clicked",
    "x_codestra_attribution": "attribution",
}
