# F-060 — HSTS includeSubDomains + preload hardcoded for one year

**Verdict:** CONFIRMED (as a low-severity hardening note)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:98-105`: inside `if not DEBUG:` the code sets `SECURE_HSTS_SECONDS = 31536000` (l.102), `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` (l.103), `SECURE_HSTS_PRELOAD = True` (l.104). None of these are env-driven.
- `DEBUG` defaults to False (`settings.py:40`), so any run without `DJANGO_DEBUG=True` gets these values.
- The header is actually emitted: `SecurityMiddleware` is installed (`settings.py:58`), and `SECURE_PROXY_SSL_HEADER` (l.105) plus Caddy's `reverse_proxy web:8000` (`Caddyfile:29`, which sets `X-Forwarded-Proto` by default) make `request.is_secure()` true for proxied requests. So responses from Django on the apex domain carry `max-age=31536000; includeSubDomains; preload`.
- Caddy serves the apex (`Caddyfile:16`) and `www` (`Caddyfile:11`) over HTTPS, so known subdomains are fine. Other subdomains are outside this repo and cannot be checked, so `includeSubDomains` is a latent risk, not a demonstrated breakage.
- Caveat on "preload is hard to undo": the `preload` directive alone does not put the domain on the list. Someone has to submit it to hstspreload.org. The directive does count as consent, so anyone can submit it. The risk is real but depends on that submission step.
- No exploit path. This is an operational/irreversibility concern, so low is correct.

## Better proposal
Keep `SECURE_HSTS_SECONDS`, but make `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` env-driven (`env.bool(..., default=False)`), or drop `SECURE_HSTS_PRELOAD` unless the domain is deliberately submitted. Accept or silence `check --deploy` W021 in line with F-021. Effort S.
