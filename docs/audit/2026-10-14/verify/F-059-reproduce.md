# F-059 (reproduce): ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS entries are not stripped

**Verdict:** CONFIRMED (latent)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:43` has `ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", ...)`, and `django/config/settings.py:107` has `CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])`. The line numbers in the finding are correct.
- Reproduced with django-environ 0.12.0 (the installed version): `X='a.com, www.a.com'` gives `env.list('X')` = `['a.com', ' www.a.com']`. The leading space is kept.
- Django compares hosts and origins exactly, so `' www.a.com'` never matches. The request gets a 400 (DisallowedHost), or the CSRF origin check fails (403). This fails closed, so there is no security impact.
- Every config example uses commas with no spaces: `.env.example:8-9`, `.github/workflows/docker-build-push.yml:19,50-51`, `.github/workflows/django.yml:43`, and `Makefile:36-38`. The local `.env` also has no `, ` in these variables. So nothing is broken today. The problem only shows up if someone adds spaces by hand.

## Better proposal
The proposed one-line fix is fine. A variant that also drops empty entries (for example from a trailing comma):
`[h.strip() for h in env.list("ALLOWED_HOSTS", default=[...]) if h.strip()]`. Do the same at line 107. Effort S.
