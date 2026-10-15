# F-122 reproduce: No favicon or apple-touch-icon

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/base.html:4-12`: `<head>` has charset, viewport, theme-color, title, stylesheet, two scripts. No `rel="icon"` or `apple-touch-icon`. Repo-wide grep for `favicon|apple-touch|rel="icon"` under `django/` and `infra/` returns nothing.
- `django/main/static/images/` holds only `default_image.png`, `hero-bg*.png`. No icon file.
- `infra/Caddyfile:18-26` serves only `/static/*` and `/media/*`; everything else, including `/favicon.ico`, goes to `reverse_proxy web:8000` (`infra/Caddyfile:29`).
- No URL pattern matches `/favicon.ico` (`django/config/urls.py:23-26`, `django/main/urls.py`), so `handler404` runs (`django/config/urls.py:33` -> `django/main/views.py:90-92`), rendering `errors/404.html`, which extends `base.html`.
- That render runs the three custom context processors (`django/config/settings.py:79-81`): `PageView` lookup, `Project.objects.count()`, active `PortfolioProfile` lookup (`django/main/context_processors.py:10,15,28-30`). So 3 DB queries plus a full template render per `/favicon.ico` request.

Nuance: "per new visitor" is roughly right; browsers cache the 404 poorly, so it can be more often. `VisitorCountMiddleware` (`django/main/middleware.py:13`) is path-scoped to `/` and `/home/`, so the counter is not inflated. Impact is cosmetic plus minor wasted work; low stays correct.

## Better proposal
Smallest fix: one `favicon.svg` in `static/images/` plus `<link rel="icon" href="{% static 'images/favicon.svg' %}" type="image/svg+xml">` in `base.html`, and in the Caddyfile `redir /favicon.ico /static/images/favicon.svg` (or `respond /favicon.ico 204`) so legacy `/favicon.ico` requests never reach Django. apple-touch-icon PNG is optional (iOS home-screen only).
