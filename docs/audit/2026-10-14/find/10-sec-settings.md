# sec-settings

Scope: `django/config/settings.py` security block, env parsing, SECRET_KEY/DEBUG handling, logging; cross-checked with `infra/Caddyfile`, `infra/docker-compose.prod.yml`, `.env.example`, `Makefile`, deploy workflow (HEAD of `dev`).

Verified OK (no finding): `SECURE_PROXY_SSL_HEADER` is safe because `web:8000` is not published in prod compose and Caddy v2 `reverse_proxy` overwrites `X-Forwarded-Proto`; Django 5.1 defaults already give `nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`, COOP, HttpOnly session cookie; cookies `Secure` in prod; `SECRET_KEY` required; DEBUG defaults to False; GitHub token is only sent as a header (`github_client.py:43`) and never logged.

## 1. Weak/placeholder SECRET_KEY and DEBUG=True are never caught (`check --deploy` not run)
- Severity: medium
- Category: security
- File: django/config/settings.py:35
- Problem: settings only reject an empty key (`settings.py:35-37`). `.env.example:2,5` ships `DJANGO_DEBUG=True` and `SECRET_KEY=your_generated_secure_key_here` (30 chars), both accepted. `make dev-up` copies the example to `.env` (`infra/scripts/ensure_env.py:16`), and the prod `.env` on the droplet is hand-made. Nothing runs `manage.py check --deploy`: `Makefile:36` runs plain `check` with `DJANGO_DEBUG=True`, and the deploy script (`docker-build-push.yml:107-109`) goes straight to `up`. A prod `.env` started from the example would serve DEBUG pages (settings, tracebacks) and sign sessions with a public key.
- Proposal: in the deploy script before `up`, run `docker compose ... run --rm web python manage.py check --deploy --fail-level WARNING` (this flags security.W009 weak key and W018 DEBUG on the real `.env`). Optionally add the same to `make verify` with `DJANGO_DEBUG=False` and a 50+ char random key so the prod block is also checked in CI.
- Effort: S
- Risk: a check failure aborts the deploy (`script_stop: true`); that is the intended behaviour, but run it once manually on the droplet first.

## 2. `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` entries are not stripped
- Severity: low
- Category: bug
- File: django/config/settings.py:43
- Problem: django-environ 0.12 `env.list` does `[x for x in value.split(',') if x]` with no strip. `ALLOWED_HOSTS=example.com, www.example.com` yields `" www.example.com"`, so that host gets 400 and the CSRF origin never matches (same for line 107). Fails closed, but confusing to debug.
- Proposal: `[h.strip() for h in env.list(...)]` on both lines, or document "no spaces" in `.env.example`.
- Effort: S
- Risk: none.

## 3. HSTS includeSubDomains + preload hardcoded for one year
- Severity: low
- Category: security
- File: django/config/settings.py:102
- Problem: any `DJANGO_DEBUG=False` run on the real domain sends `max-age=31536000; includeSubDomains; preload`. Every subdomain of the apex is then HTTPS-only in browsers for a year. `preload` has no effect unless the domain is submitted to hstspreload.org, and is very hard to undo once it is.
- Proposal: keep includeSubDomains only if all subdomains serve HTTPS; drop `SECURE_HSTS_PRELOAD` unless the domain is actually being submitted for preload.
- Effort: S
- Risk: removing preload lowers the `check --deploy` score (W021 only fires if preload is false, as a warning). Decide before adding finding 1 with `--fail-level WARNING`, or silence W021 explicitly.

## 4. Caddy-served `/static` and `/media` skip Django security headers
- Severity: low
- Category: security
- File: infra/Caddyfile:18
- Problem: `/static/*` and `/media/*` are answered by Caddy `file_server`, so they get no `X-Content-Type-Options: nosniff`, HSTS or Referrer-Policy. `/media` holds admin uploads (`models.py:59-63`). Upload validation (Pillow for images, `.md` extension) keeps the risk low, but defence in depth is missing. There is also no CSP anywhere, while `projects/detail.html:18` renders README HTML with `|safe` (sanitized by bleach, `views.py:371`).
- Proposal: add a site-level `header { X-Content-Type-Options nosniff; Referrer-Policy same-origin }` in the `https://{$APP_DOMAIN}` block. A CSP is a separate follow-up that needs a template audit for inline scripts first.
- Effort: S
- Risk: none for nosniff. A CSP could break inline scripts or styles.

## 5. `STATICFILES_STORAGE` is a dead setting on Django 5.1
- Severity: low
- Category: library
- File: django/config/settings.py:181
- Problem: Django 5.1 removed `STATICFILES_STORAGE` (replaced by `STORAGES`), and Django 5.1.15 is pinned (`pyproject.toml:10`). The line is ignored, and its comment suggests a config that does not exist.
- Proposal: delete the line (the default storage is the same).
- Effort: S
- Risk: none.

## 6. Unused `DEBUG` scheme in `environ.Env(...)`
- Severity: low
- Category: simplification
- File: django/config/settings.py:24
- Problem: `environ.Env(DEBUG=(bool, False))` declares a `DEBUG` env var that is never read. The real flag is `DJANGO_DEBUG` (line 40). This can mislead someone into setting `DEBUG=False` in `.env`, which has no effect. The comments are in Polish, while the repo convention is English.
- Proposal: `env = environ.Env()` and drop the Polish comments (lines 25, 28).
- Effort: S
- Risk: none.
