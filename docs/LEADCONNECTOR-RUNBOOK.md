# Codestra LeadConnector implementation and activation runbook

## Scope and boundary
Widget: `6ac7add4b17ff091c6b9a42c`; HighLevel location: `jpzEheys0lV7R6jsD8W9`.
This implementation adds public website chat and a local, authenticated inbound review queue. It does not activate carrier messaging, calls, marketing, or automatic Odoo/Middleware delivery. The source branches must pass protected review and exact-head CI before promotion.

## Frontend
The widget is loaded once on the explicit public route allowlist. Login, signup, billing forms, unknown routes, and authenticated application pages do not load it. Crossing the public/private boundary replaces the document before private children render; deleting a loaded script tag alone would not unload third-party code.
Set `VITE_CHAT_WIDGET_ENABLED=false` at build time to disable the frontend widget. The vendor widget ID is public; no API secret belongs in the frontend.
`nginx.conf` is the general HTTPS deployment configuration. `deploy/leadconnector-nginx-lan.conf` is a candidate of the actual mounted LAN configuration, retaining the trusted edge forwarding and private media/API routes. Apply the appropriate file only through the deployment process. Do not overwrite one with the other blindly. The LAN configuration terminates HTTP behind the trusted TLS edge; it must not upgrade LAN asset URLs to a nonexistent HTTPS port.

## Backend
`POST /api/leadconnector/webhook/` verifies the exact raw request bytes using the official Ed25519 public key and `X-GHL-Signature`. Unsigned workflow webhooks and deprecated RSA-only signatures are rejected. Payloads are bounded to 64 KiB and rate-limited. Only the configured location and exact widget can create new chat leads.
`GET /api/leadconnector/leads/` is paginated and requires `leadconnector.view_chatlead`; readback is constrained to the configured location. `GET /api/leadconnector/status/` has the same permission. Django admin provides a read-only view.
Set `LEADCONNECTOR_ENABLED=true` only after deployment and provider subscription verification. Its default is false, returning 503. Setting this flag only enables receipt processing; it does not enable outbound effects.
Run `python manage.py migrate` against the approved deployment database during the controlled release. The initial migration creates dedicated lead and receipt tables, without altering existing customer records. Do not delete receipts during rollback; their unique event keys protect against repeated deliveries.

## Consent and data
A supplied phone number, `dnd=false`, or arbitrary consent boolean is not verified opt-in evidence. Consent stays unknown unless a signed global or SMS-specific active DND condition marks it withdrawn. Withdrawal remains sticky. No event grants outbound contact permission.
The chat record retains necessary enquiry/contact fields. Receipts retain event identity, a canonical content hash and the consent determination, not raw payload bodies. Apply the organization's retention/deletion policy before enabling real intake. Signed Contact events only enrich an existing widget-attributed lead; ContactCreate events that arrive before the first widget message are ignored to avoid importing unrelated contacts. This means names/email may be absent until a later ContactUpdate. Payloads without provider timestamps use receipt order; exact chronology is unknowable when the provider omits an event clock.
The implementation does not verify HighLevel's own account workflows or auto-replies. Confirm those are disabled until separately authorized. Chat form submission is not part of automated testing.

## Provider connection and external acceptance
1. Reconcile the feature with the currently deployed source, preserving already-deployed API repairs. The original deployment is ahead of or different from main; do not deploy the feature branch wholesale over those changes.
2. Complete independent review and required exact-SHA GitHub checks, then create a tested deployment image and backup/rollback manifest.
3. Verify publicly reachable HTTPS for `codestra.co`, not only LAN reachability. Install the widget CSP configuration on the actual serving proxy and verify the real loader and inner resources in a browser. Add any further provider origins only after observation and review; do not use unsafe script allowances.
4. In the HighLevel Marketplace application's webhook settings, subscribe the Codestra location to InboundMessage, ContactUpdate and ContactDndUpdate, with the deployed URL `https://codestra.co/api/leadconnector/webhook/`. The embed itself does not register this subscription. An unsigned workflow callback is not a substitute.
5. Enable local intake and verify one authorized real signed event, then duplicate delivery/readback without sending SMS or calls. Confirm the widget attribution field is present in the actual event; unmatched events are intentionally ignored.
6. Have the business owner review the website terms, privacy notice, business identity and widget consent disclosures. Confirm the submitted public page has no competing SMS-consent form before using the compliance checkbox. Technical test success is not carrier or HighLevel approval.

## Reference contracts
- https://marketplace.gohighlevel.com/docs/webhook/WebhookIntegrationGuide/
- https://marketplace.gohighlevel.com/docs/webhook/InboundMessage/
- https://marketplace.gohighlevel.com/docs/webhook/ContactDndUpdate/
- https://help.gohighlevel.com/support/solutions/articles/155000008307-pre-built-a2p-campaign-registration-with-chat-widget

## Verification reproduction
Frontend: `npm ci`, `npm test`, `npm run lint`, `npm run build`, `npm run audit:production` using the repository Node requirement.
Browser: run `scripts/verify-chat-widget.cjs` with Playwright 1.56.1 and its matching Chromium. Set `CHAT_TEST_BASE_URL` to an isolated deployed build and `CHAT_TEST_OUTPUT` to the result path. Contract checks mock the vendor; the final vendor availability probe does not. Local backend API calls are mocked because this is a static preview. No contact form is submitted.
Backend: run the complete Django suite with `CORE.test_settings` for SQLite, then `CORE.leadconnector_pg_test_settings` for isolated PostgreSQL. Supply `LC_PG_HOST` and `LC_PG_PASSWORD`, using only an ephemeral test database named `chat_test` and user `chat_test`. The concurrency regression is skipped on SQLite and must pass on PostgreSQL. Run `manage.py check` and `manage.py makemigrations --check --dry-run` as additional gates.

## Rollback
Disable the feature flag, restore the previous verified image and serving configuration, and retain the receipt tables. Do not drop production data, force-push branches or weaken checks to obtain a green status. The dedicated LAN preview is separate from the existing production containers.
