# Repository Profile — `backend2`

## Identity

- **Repository:** `appolon1908-hue/backend2`
- **Category:** Corporate backend — Codestra CMS
- **Visibility:** `private`
- **Default branch:** `main`
- **Authority:** Codestra CMS backend; overlaps with `codestra-backend` and needs a canonical decision
- **Status:** Django CMS/API implementation with same-origin production routing.

## Purpose

Django CMS and API serving `/api`, administration, media, static assets, health, and sitemap for the Codestra website.

## Owns

- Codestra CMS content and administration
- Same-origin website API
- Backend media/static and operational endpoints

## Does not own

- Trading-platform services
- Unreconciled duplicate backend behavior
- Frontend build

## Key integrations

- `codestra` frontend
- PostgreSQL
- Redis
- Caddy same-origin routing

## Current priorities

1. Decide whether this or `codestra-backend` is canonical
2. Create a migration/deprecation plan for the noncanonical backend
3. Pin immutable images and backup/restore evidence
4. Document API compatibility with the frontend

## Governance and safety

- Target promotion model: `feature/docs/fix/security/upgrade -> development -> test -> staging -> production -> main`.
- Use pull requests and exact-head/merge-result validation; merging source never authorizes deployment.
- Never commit secrets, credentials, private keys, customer data, database dumps, or secret-bearing evidence.
- Production images and releases must be immutable; mutable `latest` tags are not release authority.
- This document does not deploy software, enable live effects, apply identity state, alter DNS/firewalls, reload Caddy, expose native ports, initialize OpenBao, or activate production.

## Account-wide catalog

See `appolon1908-hue/documentaions/REPOSITORY_CATALOG.md`.
