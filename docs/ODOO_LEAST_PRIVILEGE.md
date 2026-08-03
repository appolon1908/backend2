# Odoo adapter least privilege

The Codestra service identity must be able to authenticate, create the
approved `crm.lead` fields, and read only the campaign, team, source, and
medium records needed to resolve routing. It must not administer users,
install modules, manage databases, delete records, or write unrelated models.

The candidate adapter sends only the stored `submission_id` and server-side
resolved mapping; browsers cannot call this boundary. Live Odoo writes remain
disabled (`LEAD_DELIVERY_MODE=mock`) until an owner supplies staging schema
evidence, a controlled receiver/account, field mappings, and explicit
authorization. Without those staging credentials and evidence,
`ODOO_LEAST_PRIVILEGE_GATE` remains `BLOCKED`.
