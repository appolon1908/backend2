# Marketplace security

The catalog is deny-by-default. Mutation endpoints require authenticated tenant/workspace context and idempotency. Subscription and entitlement references are mandatory; middleware performs the authoritative decision. Package verification is fail-closed. Test unpublished access, cross-tenant requests, entitlement and signature bypass, checksum tampering, permission expansion, traversal, upload validation, stored XSS, abuse, and rate limits.
