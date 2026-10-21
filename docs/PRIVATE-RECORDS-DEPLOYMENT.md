# Private records and local signup recovery (GH18)

This change protects sensitive records without closing public marketing content or intake.

| Surface | Public access | Staff access |
| --- | --- | --- |
| Taxpayer registration | Submit only | Read/update/delete |
| Contact and billing interest | Submit only | Read their own separate collections |
| Job openings | Read/apply | Manage openings and read applications/answers |
| Tax and career documents | Denied | Authenticated attachment download |
| Customers | Denied | Read/mutate |
| Blog | Read; signed-in users can like/comment | Publish/edit/moderate |
| Employee directory | Explicit public field allowlist | Existing complete response |
| Calendar | Authentication required; unavailable integration returns 503 | Existing mutation policy |

## Required deployment steps

Apply migrations through `auth_app.0005_user_crm_sync_payload` (includes PR17 migration 0004).
The additive JSON field stores the signup contact payload before enqueueing and never includes a password.

Route **both** `/media/tax/` and `/media/career/` to Django before any generic public media alias.
An example server-level include is `deploy/nginx-private-media.conf`; adapt only the backend upstream hostname/port to the deployment.
Django matches a registered TaxPayerMedia or CareerApplication file, verifies staff authentication, and streams an attachment with private/no-store caching.
Never serve those directories directly through nginx, a CDN, another static mount, or a public bucket.
Existing attachment URLs remain valid for authenticated staff cookie sessions.

For a LAN-only HTTP deployment, set `AUTH_COOKIE_SECURE=False` together with `CSRF_COOKIE_SECURE=False` and `SESSION_COOKIE_SECURE=False` in the isolated runtime settings.
Keep `DEBUG=False`; HTTPS deployments retain secure cookies.
No provider credentials or production effect switches are enabled by this change.

## Signup and Middleware semantics

Signup persists locally in one database transaction and returns `crm_sync: pending`.
Broker or missing-integration failures keep the durable intent pending with a sanitized error.
The task freezes legacy unsent payloads before retry; profile edits cannot change a request under the same idempotency key.
The client omits a changing correlation header so Middleware derives correlation consistently from the stable idempotency key.

A valid accepted operation is recorded as `submitted`.
Neither an acceptance receipt nor a completed operation string alone certifies Odoo readback:
`crm_synced_at` and `odoo_id` remain unset. CMS receipt status follows the same distinction.
Provider reconciliation and verified Odoo linkage remain a separate integration gate.

After Middleware and the worker are configured, an operator may recover a bounded batch:

```sh
python manage.py retry_pending_signups --limit 100
```

The command does nothing when integration settings are absent, accepts limits 1–1000, and selects only frozen signup intents without an existing Odoo linkage or operation ID. Legacy/admin accounts without an intent are excluded.
No periodic scheduler or live provider activation is added.

## Verification

The full Django test suite covers seeded unauthorized reads, staff reads/mutations, public intake, private document byte delivery and traversal, public directory field filtering, broker failures, payload/idempotency reuse, invalid refresh cookies, inactive users, and health requests through the production middleware list.
Run `python manage.py test` with isolated test settings as CI does; never use production databases for these tests.
