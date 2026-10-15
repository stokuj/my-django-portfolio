# F-109 - No brute-force or rate-limit protection on /admin/login/ (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `django/config/urls.py:24` mounts `admin.site.urls` at the default `admin/` path; no env-driven prefix.
- `pyproject.toml:7-22`: no lockout/rate-limit package (no django-axes, django-ratelimit, etc.).
- `django/config/settings.py:168-170`: only `ModelBackend`; no custom backend adding throttling. No `PASSWORD_HASHERS` override, so Django 5.1 default PBKDF2 (870k iterations) is used.
- `infra/Caddyfile:16-29`: only `/static/*` and `/media/*` are handled locally; everything else, including `/admin/*`, goes to `reverse_proxy web:8000` with no `remote_ip` matcher, `basic_auth`, or rate limit. `infra/docker-compose.prod.yml:154` uses stock `caddy:2` (no rate_limit module).
- `infra/docker-compose.prod.yml:44-46`: `gunicorn config.wsgi:application --bind 0.0.0.0:8000` with no `--workers`; no `gunicorn.conf.py` exists in `django/` (the working dir), so it runs 1 sync worker. Each POST to `/admin/login/` costs a full PBKDF2 hash (ModelBackend also hashes for unknown usernames to equalize timing), so repeated login POSTs serialize the only worker -> cheap DoS of the whole site.
- Attack path is reachable: the admin login form is public over HTTPS; CSRF only requires fetching the form first.

Mitigating context (does not refute): exploitability of guessing depends on admin password strength; severity stays medium (not critical) since no known weak credential.

## Better proposal
Zero-dep and smallest: in Caddy, put `/admin*` behind `basic_auth` (or a `remote_ip` allowlist) before `reverse_proxy`. This blocks both guessing and the PBKDF2 CPU cost at the proxy. django-axes only adds lockout; it still runs the hash per attempt until lockout and needs a migration. Optionally also set gunicorn `--workers 2-3` (see F-009).
