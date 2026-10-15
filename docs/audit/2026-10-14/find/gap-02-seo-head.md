# gap-seo-head

Scope: SEO, social metadata and `<head>` of `django/main/templates/base.html` and page templates, URL routing, Caddy, settings at HEAD (branch dev).

Verified OK (no finding): `<html lang="en">` is set (base.html:3). Trailing-slash variants (`/about` vs `/about/`) are 301-redirected by `CommonMiddleware` with default `APPEND_SLASH` (settings.py:62), so they are not duplicates. `www` -> apex is 301-redirected by Caddy (infra/Caddyfile:11-13). Error pages 404/500 define a correct `title` block (errors/404.html:3, errors/500.html:3) and are served with real 404/500 status (views.py:90-97).

## G-SEO-1 No meta description on any page
- Severity: medium | Category: frontend | Effort: S
- File: django/main/templates/base.html:5-9
- Problem: The head has only charset, viewport, theme-color, title, stylesheet. No `<meta name="description">` anywhere in templates (grep returns none). Search engines generate snippets from random page text. The data already exists in context: `profile_home_intro`, `profile_about_intro` (context_processors.py:41-42) and `Project.short_description` (models.py:68).
- Proposal: In base.html add `<meta name="description" content="{% block meta_description %}{{ profile_home_intro }}{% endblock %}">`; override in about.html with `profile_about_intro` and in projects/detail.html with `project.short_description`.
- Risk: None; additive markup.

## G-SEO-2 Home and projects index have no title block; base default ignores site_name
- Severity: medium | Category: frontend | Effort: S
- File: django/main/templates/base.html:8; django/main/templates/pages/home.html:1-3; django/main/templates/projects/index.html:1-3
- Problem: home.html and projects/index.html define no `{% block title %}` at all, and base.html hardcodes the fallback `My Portfolio` instead of the editable `site_name` (context_processors.py:37, already used in the navbar at base.html:50). about.html:3 and projects/detail.html:4 use the wrong block name `page_name` (that part is F-034; not repeated here). Net result: every non-error page has the same title, including each blog post.
- Proposal: base: `{% block title %}{{ site_name }}{% endblock %}`; home: keep default; projects/index: `{% block title %}Projects | {{ site_name }}{% endblock %}`; fix F-034 the same way for about/detail.
- Risk: None.

## G-SEO-3 Duplicate content at `/` and `/home/` with no canonical link
- Severity: medium | Category: frontend | Effort: S
- File: django/main/urls.py:5-6; django/main/templates/base.html:5-9
- Problem: `""` and `"home/"` both route to `views.home` and return 200 with identical HTML. `{% url 'home' %}` resolves to `/home/` (later pattern wins, F-089), so the navbar logo (base.html:50) links internally to the duplicate URL, which makes crawlers index both. No `<link rel="canonical">` exists in any template.
- Proposal: Replace `path("home/", views.home, ...)` with `path("home/", RedirectView.as_view(url="/", permanent=True))` (also resolves F-089). Optionally add `<link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">` in base.html to strip query strings.
- Risk: `VisitorCountMiddleware` checks `/home/` (middleware.py:13); after the redirect it only needs `/`. Low.

## G-SEO-4 No Open Graph / Twitter card tags
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/base.html:5-9
- Problem: No `og:*` or `twitter:*` meta tags anywhere. Links shared on LinkedIn/GitHub/Slack (the typical channels for a portfolio) render as bare URLs without title, description or image.
- Proposal: In base.html add `og:title` (reuse title block), `og:description` (reuse meta_description block), `og:type=website`, `og:url` (same as canonical), `og:image` (`project.thumbnail.url` on detail, else `static/images/default_image.png` as absolute URL), and `<meta name="twitter:card" content="summary_large_image">`.
- Risk: `og:image` must be an absolute URL; relative `{% static %}` paths are ignored by scrapers.

## G-SEO-5 No robots.txt; request falls through to Django 404
- Severity: low | Category: ops | Effort: S
- File: infra/Caddyfile:16-30; django/main/urls.py:4-21
- Problem: No robots.txt route in Django and no Caddy rule. `/robots.txt` hits `reverse_proxy web:8000` (Caddyfile:29) and renders the full 404 template via `handler404` (views.py:90-92), running all context processors (3 DB queries, context_processors.py:10,15,29) on every crawler hit. `/admin/` and `/admin-tools/` are not disallowed for crawlers.
- Proposal: In Caddy main site block: `respond /robots.txt "User-agent: *\nDisallow: /admin/\nDisallow: /admin-tools/\n" 200` (plus a `Sitemap:` line if G-SEO-6 is done). No Django code needed.
- Risk: None.

## G-SEO-6 No sitemap
- Severity: low | Category: frontend | Effort: S
- File: django/config/settings.py:47-55; django/config/urls.py:23-26
- Problem: `django.contrib.sitemaps` is not installed and no `/sitemap.xml` route exists. Blog posts (`/blog/<slug>/`) are discoverable only through internal links.
- Proposal: Add `django.contrib.sitemaps`, one `Sitemap` for `Project.objects.filter(blog=True).exclude(blog_url=None)` (needs `Project.get_absolute_url` or `location()`), one for static names `home`, `about`, `projects`; route `sitemap.xml`. Skip if the site stays at a handful of linked pages: internal links already cover crawl.
- Risk: Without `django.contrib.sites`, sitemaps uses `RequestSite` (host from request), which is fine behind Caddy with correct `ALLOWED_HOSTS`.

## G-SEO-7 No favicon or apple-touch-icon
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/base.html:5-9; django/main/static/images/
- Problem: No `<link rel="icon">` / `apple-touch-icon` in head and no icon file in static/images (only default_image.png and hero-bg*.png). Browsers request `/favicon.ico`, which Caddy proxies to Django (Caddyfile:29) and gets a rendered 404 with DB queries, once per new visitor; tabs and bookmarks show a generic icon.
- Proposal: Add `static/images/favicon.svg` (+ 180x180 `apple-touch-icon.png`) and `<link rel="icon" href="{% static 'images/favicon.svg' %}" type="image/svg+xml">` / `<link rel="apple-touch-icon" href="...">`. Optionally Caddy `redir /favicon.ico /static/images/favicon.svg`.
- Risk: None.
