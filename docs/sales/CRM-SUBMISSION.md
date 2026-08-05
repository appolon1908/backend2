# CRM submission

Validated prospects pass duplicate, consent, suppression, do-not-call, and recent-contact review. Server C submits an idempotent command to middleware. Middleware authorizes and writes Odoo, then returns a CRM reference for reconciliation. Server C has no Odoo database credentials and never inserts a VICIdial list.
