# F-060 — HSTS includeSubDomains + preload hardcoded for one year

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:98-105`: inside `if not DEBUG:` the values are hardcoded, with no env override: `SECURE_HSTS_SECONDS = 31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`, `SECURE_HSTS_PRELOAD = True`.
- `django/config/settings.py:40`: `DEBUG = env.bool("DJANGO_DEBUG", default=False)`, so any run without `DJANGO_DEBUG` set picks the production branch.
- `django/config/settings.py:58`: `SecurityMiddleware` is enabled. It sends the header only on secure requests. `SECURE_PROXY_SSL_HEADER` (line 105), together with Caddy's `reverse_proxy web:8000` (`infra/Caddyfile`), which sets `X-Forwarded-Proto` by default, makes the request secure, so Django responses on the apex domain do carry `max-age=31536000; includeSubDomains; preload`.
- Mitigating facts:
  - `infra/Caddyfile` serves only the apex domain and `APP_WWW_DOMAIN`, both over HTTPS, so no known subdomain breaks today.
  - The `preload` directive alone does nothing until the domain is submitted to hstspreload.org. It does, however, satisfy the requirements a submission checks, so lock-in is one form away.
  - Static and media files served directly by Caddy do not carry the header, but HTML responses do.
- The finding's description matches HEAD exactly. The impact is hypothetical (a future HTTP-only subdomain, or an accidental preload submission), so low is the right severity.

## Better proposal
Make the HSTS settings env-driven with safe defaults, for example `SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)` and the same pattern for `INCLUDE_SUBDOMAINS`. Turn preload on only after a deliberate submission to hstspreload.org. Decide together with F-021, because `check --deploy` raises W021 when preload is off.
