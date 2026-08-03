# Secret-scan triage

The only historical Gitleaks findings are two `generic-api-key` matches in the
vendored drf-yasg Redoc bundle at commit
`aa0e4171c04ef9c516b0bcc068bd6bb246377d6a`. The matched values are JavaScript
property names (`excludeParentKeys`), not credentials. The allowlist is scoped
to the exact commit, path, rule fingerprint and line; global rule suppression
is not used. Re-run `gitleaks detect --log-opts='--all'` in CI and review any
new finding as a failure.
