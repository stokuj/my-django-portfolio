# F-109 (worth): No brute-force or rate-limit protection on /admin/login/

**Verdict:** CONFIRMED (worth fixing, but use a different fix than django-axes)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `django/config/urls.py:24` mounts `admin.site.urls` at the default `admin/`.
- `django/config/settings.py:168-170` uses only `ModelBackend`, so admin login is password-only. No OAuth or 2FA in front of it.
- `pyproject.toml:7-22` has no lockout or rate-limit package (no axes, django-ratelimit and similar).
- `infra/Caddyfile:16-29` only special-cases `/static/*` and `/media/*`; everything else, including `/admin/*`, goes to `reverse_proxy web:8000` with no restriction. `infra/docker-compose.prod.yml:154` uses stock `caddy:2`, which has no rate-limit module.
- `infra/docker-compose.prod.yml:46` runs `gunicorn` with no `--workers`, so it uses the default of 1 sync worker. Each POST to the login form runs a PBKDF2 hash, and a CSRF token is easy to get from the GET. That makes login spam an easy way to tie up the whole site.
- Mitigation: `settings.py:125-138` enables the standard password validators, so an online guessing attack only works if the password is weak. That keeps this at medium, not high.
- No doc or commit records a decision to leave the admin open. `git log` shows only "Add GitHub heatmap, admin OAuth & caching" (7af03e4), and that OAuth is for the GitHub heatmap token, not admin login.

## On the proposal
- django-axes adds a dependency, INSTALLED_APPS and middleware config, a migration and tests. That is a lot for a site with a single admin. It also does nothing for the CPU-DoS part: axes still runs in the Django worker, and failed attempts before lockout still hash.
- A Caddy IP allowlist risks locking the owner out from a new IP. The finding already notes this.

## Better proposal (smallest diff, zero deps)
Put Caddy's built-in `basic_auth` in front of `/admin*` in `infra/Caddyfile` (in the apex site block, before `reverse_proxy`):

```
basic_auth /admin* {
    {$ADMIN_BASIC_USER} {$ADMIN_BASIC_HASH}
}
```

Generate the hash with `caddy hash-password` and add the two vars to `.env.example`. This blocks unauthenticated requests before they reach the single gunicorn worker, which removes the CPU-DoS path, and it adds a second credential without locking the owner out by IP. Moving the admin path through an env var is optional obscurity and adds little once basic_auth is in place.
Effort: S. Risk: the owner must keep the basic-auth credential. Check that the compose `caddy` service gets the new env vars.
