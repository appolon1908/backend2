# Odoo 20 → Codestra CRM Dashboard Integration

## Components and boundaries

- Odoo 20 Community `callcenter_crm 20.0.1.5.0` (server-3 staging) exposes only three read-only routes: `GET /callcenter/api/v1/overview`, `/campaigns`, `/leads`. Its new `codestra-crm-read` bearer scope is distinct from Odoo's general RPC scope.
- Django backend2 PR #24 publishes `GET /api/cms/odoo-crm/{overview,campaigns,leads}/`. Requests must be authenticated Codestra Django users with `is_staff=True` **and** membership in `Codestra Call Center Super User` (or Django superuser). A generic staff user is not sufficient.
- Odoo's configured bearer account **must** have the `Call Center Super User` role; Django requires its response `role=superuser` and `schema_version=1`. It cannot use a general RPC key or an agent-scoped key.
- Codestra React frontend PR #55 makes authenticated read-only requests to the Django proxy. **Never** expose Odoo API keys in Vite environment variables, JavaScript, browser storage, or network responses.

## Secure operator steps — staging only

1. In the Odoo 20 UI, have the authorized call-center administrator choose the intended account and select **Codestra CRM Dashboard — Read Only** when creating an API key. Prefer short expiration/rotation. Do not use the generic **RPC** scope.
2. In Django admin, assign the `Codestra Call Center Super User` group to each permitted Codestra staff account; confirm `is_staff=True`. Do not use `is_staff` alone as the access rule. Treat a Django identity as a dashboard administrator, **not** automatically as an agent or supervisor's Odoo identity.
3. Store the Odoo key securely as the backend-only `ODOO_API_TOKEN` environment secret, and set `ODOO_BASE_URL` to a verified HTTPS CRM ingress endpoint. HTTP is supported only with the explicit allowlisted private Docker service host `odoo` or `compose-odoo-1`. The backend never follows redirects.
4. Keep the Django→Odoo network path private, with scope-limited credentials and no exposed database ports. Do not connect the frontend browser directly to Odoo using this API key.
5. On a staging instance, verify unauthenticated requests to `/api/cms/odoo-crm/overview/` return **401** and ordinary staff return **403**, while the explicitly bound dashboard admin receives JSON HTTP **200**, `role=superuser`, `schema_version=1`.
6. Check populated campaigns and leads using at least two synthetic campaigns with role/membership isolation. Confirm empty state, pagination, button navigation, response cache headers, browser logout, phone/mobile view, and HTTP 401/403/503 denial paths. Use **isolated staging records**, never sample writes in production.
7. Retain production GO=NO until independent review and the protected canonical repository identity catalog is updated. Current `Production orchestrator contract` is blocked by stale identity records for repos transferred from `appolon1908-hue` to `appolon1908`; do not fabricate green checks or edit immutable hashes just to bypass the gate.

## Verified evidence and remaining gaps (2026-10-08)

- Odoo 20 source/merge-result CI, hierarchy, security, and legacy addon CI passed at scoped release `3f8d9e36c9b49441d7c714474e9ab3a54dd84fbc`.
- Staging Odoo is running addon `20.0.1.5.0` and the new scope is registered in `res.users.apikeys.description`. HTTP login 200; three routes 401 anonymous.
- An isolated Django preview (not the real backend) is at `10.0.0.218:3095`, backed by **disposable SQLite** and **no API key**. Codestra's isolated React preview at `10.0.0.218:3096/auth/dashboard/crm` proxies the CRM path to it and returns real 401 JSON for anonymous users.
- The isolated browser end-to-end harness at `/srv/codestra/verification/odoo20-e2e-connected-preview-20261008/e2e-results.json` passed **21/21** checks, including an actual frontend→Django anonymous denial and synthetic interactive campaigns/leads, filtering, detail expansion, mobile and error states. Positive campaign datasets in this browser test were **intercepted fixtures**, not confirmed business data.
- Full authenticated positive Django→Odoo→React live-data certification is **pending operator-issued, purpose-scoped Odoo key, Django staff group assignment, and real campaign data**. Do not misrepresent it as complete. Public lead-create endpoints in older backend2 code are a separate write-integration track and must remain dark until Odoo 20/Middleware migration.
