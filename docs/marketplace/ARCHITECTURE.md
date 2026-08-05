# Marketplace architecture

Server C owns public catalog presentation and validates request shape. It never provisions a tenant or executes package commands. Authenticated mutation requests carry tenant, workspace, subscription, entitlement, idempotency, and audit context to the middleware gateway at `65.109.65.169`. Middleware owns authorization, approval, persistence, dispatch, reconciliation, and production activation.

Products are private by default (`DRAFT`). Only `STAGING_VISIBLE` and `PRODUCTION_VISIBLE` records can be returned by public APIs. Installation, update, rollback, and trial actions fail closed when middleware is unavailable.
