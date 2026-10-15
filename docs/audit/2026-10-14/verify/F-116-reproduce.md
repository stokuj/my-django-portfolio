# F-116 — No sitemap (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:47-55`: INSTALLED_APPS has no `django.contrib.sitemaps` (nor `django.contrib.sites`).
- `django/config/urls.py:23-26`: only `admin/` and `include("main.urls")`; `django/main/urls.py:5-16` has no sitemap route.
- Repo-wide grep for `sitemap`/`robots` (excluding lockfiles, migrations, audit docs) returns nothing; `infra/Caddyfile` serves no static sitemap.xml or robots.txt.
- Blog pages exist at `blog/<slug:blog_slug>/` (`django/main/urls.py:10`), resolved via `Project(blog=True, blog_url=slug)` (`django/main/views.py:401`), so the proposed queryset matches real routing.
- Not a bug: crawlers still reach posts through internal links. SEO nicety only, so low is right.

## Better proposal
Same as proposed, kept minimal: one `Sitemap` for `Project.objects.filter(blog=True).exclude(blog_url__isnull=True).exclude(blog_url="")` with `location` = `reverse("blog_detail", args=[obj.blog_url])` and `lastmod` = `date`, plus a static one for `home`/`about`/`projects`. Only `django.contrib.sitemaps` is needed in INSTALLED_APPS. If added, also add a `robots.txt` line pointing to it. Skip it entirely if search indexing is not a goal.
