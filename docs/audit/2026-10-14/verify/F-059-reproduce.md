# F-059: ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS entries are not stripped (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning
- `django/config/settings.py:43` `ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", ...)` and `:107` `CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", ...)`. Neither strips the entries.
- Reproduced with the installed django-environ 0.12.0: `Env().list('X')` with `X='a.com, www.a.com'` returns `['a.com', ' www.a.com']`.
- Reproduced with Django: `validate_host('www.a.com', ['a.com', ' www.a.com'])` returns `False`, so the host gets a 400 (DisallowedHost). A CSRF origin with a leading space would also never match.
- It fails closed, so there is no security impact. The bug is latent: every value in the repo has no spaces (`.env.example:8-9`, `Makefile:36-38`, `.github/workflows/*.yml`), and compose passes `${ALLOWED_HOSTS}` through unchanged (`infra/docker-compose.prod.yml:55-56`). It would only show up if someone hand-edits the prod `.env` with spaces.

## Better proposal
The proposal works as written: `[h.strip() for h in env.list(...)]` on lines 43 and 107. A cheaper alternative is a one-line note in `.env.example` that says "comma-separated, no spaces".
