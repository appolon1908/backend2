# Codestra CMS backend

Django API used by the Codestra React frontend. Production traffic uses one origin:

- `https://codestra.co/` serves the frontend.
- `https://codestra.co/api/` serves this API.
- `/admin/`, `/static/`, `/media/`, `/healthz/`, and `/sitemap.xml` are routed to this service.

## Local Docker stack

Copy `.env.example` to `.env`, replace every placeholder, then run:

```bash
docker compose up --build -d --wait
docker compose exec web python manage.py test auth_app.tests payment_app.tests
```

PostgreSQL and Redis are internal-only. The web container runs as UID/GID `10001` and uses Gunicorn rather than Django's development server.



## Codestra integration authority

Effect-capable CRM/Odoo writes must go through Codestra Middleware; this backend
must not post directly to Odoo. Configure MIDDLEWARE_BASE_URL,
MIDDLEWARE_ACCESS_TOKEN, and MIDDLEWARE_TENANT_ID with a service identity
accepted by Middleware. Middleware owns idempotency, the command ledger, Odoo
adapter execution, retries, and reconciliation.

Stripe payment amounts are server-authoritative. Clients submit a product_code;
the amount is resolved from the server-side PAYMENT_PRICE_CATALOG. Never accept
or trust a browser-supplied payment amount.

## Production

The combined manifest is `deploy/compose.production.yaml`. Caddy obtains and renews TLS certificates and routes the frontend and backend by path. Production requires:

- a private `/srv/codestra/.env` created from `.env.example`;
- `FRONTEND_IMAGE` and `BACKEND2_IMAGE` set to immutable GHCR tags;
- DNS `A`/`AAAA` records pointing to the deployment host;
- ports 80 and 443 reachable from the Internet.

Before every upgrade:

```bash
docker compose -f compose.production.yaml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" -Fc -f /tmp/predeploy.dump
```

Verify the dump checksum and restore it into a separate database before relying on it. Roll back by restoring the dump and starting the previous immutable frontend/backend image tags.

Never commit `.env`, database dumps, generated static files, access tokens, or private keys.
