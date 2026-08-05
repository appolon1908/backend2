# Marketplace runbook

1. Confirm `/api/v1/marketplace/health` and middleware reachability.
2. Confirm automatic installation, publication, and production activation flags are false.
3. Validate manifest signature/checksums and compatibility in staging.
4. Submit through middleware with an idempotency key and approval reference.
5. Reconcile the returned request reference. On failure, pause requests; do not run package commands on Server C.
