# Localization API

- `GET /api/v1/localization/config` returns supported and fallback locales.
- `GET /api/v1/localization/country` performs server-side GeoLite2 lookup and returns only country code, suggested locale and support status.
- `POST /api/v1/localization/preference` validates the locale and stores an HTTP-only preference cookie.
- `GET /api/v1/localization/messages/:locale` reports bundled-catalog version information without exposing filesystem paths.

Only `REMOTE_ADDR` is trusted by default. `X-Forwarded-For` is read only when `REMOTE_ADDR` exactly matches a configured `TRUSTED_PROXY_IPS` entry. Raw IP addresses are neither returned nor stored for localization.

Lead submissions accept `en`, `es`, and `fr`, while mapping corresponding legacy language names for backward compatibility. They record `preferred_language`, `content_locale`, `country_code`, `locale_source`, and `translation_version`. Odoo language record IDs remain server-controlled and require schema confirmation before live delivery.
