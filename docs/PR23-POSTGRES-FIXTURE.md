# Backend PR23 PostgreSQL fixture and source-binding change

This candidate retains the repository's fail-closed service-container policy. It
adds one exact-byte configuration binding for `.github/workflows/backend-postgres.yml`
in `appolon1908/backend2` using the existing configuration-registry mechanism.
It does not grant generic service/container authority or alter classification code.

The fixture uses a GitHub-hosted Ubuntu runner, PostgreSQL 16, synthetic credentials,
no production secrets, no persistent host volumes, a localhost-only test connection,
a read-only GitHub token, and `LEADCONNECTOR_ENABLED=false`. It runs the full Django
suite, including the two-delivery PostgreSQL transaction regression. It is not a
production deployment, provider subscription, messaging activation, or approval.

The initial exact-source PostgreSQL run 37843960737 passed. The policy correctly
rejected the previously unregistered executable service configuration in run
37843960638. A new failing regression reproduced that precise absence before this
binding was added. Seven fixture regressions cover exact approval, single-byte drift,
image changes, self-hosted-runner substitution, other repositories, other paths,
and synthetic/read-only/disabled configuration. Existing identity and mutation
negative regressions remain enforced.

The backend's release-validator executable binding is now separate from the
frontend's existing binding. Frontend, provider, runtime, and image authorities are
not transferred. Only the backend normalized policy fingerprint, exact validator
hash, and complete candidate source closure are refreshed. Final exact-head checks
and independent review are still required before protected merge.
