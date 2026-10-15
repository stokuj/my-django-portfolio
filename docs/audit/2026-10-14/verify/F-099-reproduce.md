# F-099 — Static assets served uncompressed and without cache headers

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `infra/Caddyfile:16-30`: the apex site block has `handle /static/*` -> `root * /srv` + `file_server` (lines 18-21) and the same for `/media/*` (23-26). No `encode` directive anywhere in the file, no `header Cache-Control` for any path. Claim holds as written.
- `django/config/settings.py:181`: `STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"` -> no hashed file names. Templates reference unhashed paths via `{% static %}` (`django/main/templates/base.html:9-11`: `css/style.css`, `js/theme-toggle.js`, `js/mobile-menu.js`). So long/immutable caching without hashing would serve stale CSS/JS after deploy, as the finding says.
- `collectstatic` runs at container start (`infra/docker-compose.prod.yml:45`), so a Manifest storage switch would fail startup (not just CI) on a missing reference — the stated risk is real.
- Mitigation that keeps it low: Caddy `file_server` emits `ETag`/`Last-Modified`, so browsers revalidate with 304s; cost is extra round trips and uncompressed CSS/JS (style.css is the minified Tailwind build), not correctness.

## Nuance the finding misses
- Project pins `django==5.1.15` (`pyproject.toml:10`). `STATICFILES_STORAGE` was removed in Django 5.1 in favor of `STORAGES`, so line 181 is a dead setting. The fix must use `STORAGES = {"default": {...FileSystemStorage}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"}}`, not edit `STATICFILES_STORAGE`.
- Manifest storage also makes `{% static %}` raise in `DEBUG=False` for missing files (tests run with DEBUG=True, so they would not catch it); `hero_section.html:2` uses a dynamic `{% static hero_background %}` — verify every value of `hero_background` exists.

## Better proposal
1. Caddyfile: add `encode zstd gzip` inside the apex block (S, zero risk) — do this alone first.
2. Replace dead `STATICFILES_STORAGE` with `STORAGES[...]` using `ManifestStaticFilesStorage`; run `collectstatic` in `make verify`/CI.
3. Only then add `header Cache-Control "public, max-age=31536000, immutable"` inside `handle /static/*`. Do not apply it to `/media/*` (unhashed, user-replaceable).
Effort: S for step 1, M overall.
