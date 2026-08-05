# Package manifests

Every package declares code, version, publisher, platform version, files, checksums, permissions, capabilities, connectors, feature flags, database changes, rollback version, risk level, and signature reference. Validation rejects missing signatures, mismatched checksums, unsupported versions, unknown permissions, undeclared connectors/database changes/external calls, and missing rollback versions. Verification is required before staging approval; Server C never installs packages.
