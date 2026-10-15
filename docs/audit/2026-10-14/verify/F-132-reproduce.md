# F-132 (reproduce): No robots.txt; request falls through to Django 404

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- No `robots.txt` file, route or template anywhere in the repo (rg for `robots|sitemap` outside docs: no hits).
- `infra/Caddyfile:16-30`: only `/static/*` and `/media/*` are handled by `file_server`; everything else, including `/robots.txt`, goes to `reverse_proxy web:8000` (line 29).
- `django/config/urls.py:23-26` + `main.urls`: no matching pattern, so Django uses `handler404` (`urls.py:33`) -> `views.py:90-92` renders `errors/404.html`, which extends `base.html`.
- Rendering with `RequestContext` runs the three custom context processors (`settings.py:79-81`): `Project.objects.count()` (`context_processors.py:10`), `PageView...first()` (`:15`), `PortfolioProfile...first()` (`:29`). 3 DB queries per hit, as claimed.
- `VisitorCountMiddleware` (`middleware.py:13`) only touches `/` and `/home/`, so no extra write.
- Claim that `/admin/` and `/admin-tools/` are not disallowed is trivially true (no robots.txt at all).

## Nuance
- Impact is cosmetic: a crawler fetches robots.txt roughly once per day; 3 cheap queries is negligible. Low is correct.
- `/admin-tools/*` endpoints are `@require_POST` (`views.py:423,448`), so crawlers cannot reach them via GET anyway; listing them in robots.txt adds nothing and advertises internal paths. `/admin/` is login-gated; disallowing it is optional hygiene, not security.

## Better proposal
Caddy only, inside the apex block before `reverse_proxy`:
```
respond /robots.txt "User-agent: *
Disallow: /admin/
" 200
```
Drop the `/admin-tools/` line. Add `Sitemap:` only if F-116 lands.
