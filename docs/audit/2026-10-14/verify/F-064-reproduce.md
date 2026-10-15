# F-064 (reproduce lens): Three uncached queries per template render

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning (verified at HEAD)
- Three DB queries per `RequestContext` render: `Project.objects.count()` (django/main/context_processors.py:10), `PageView.objects.filter(id=1).first()` (:15), `PortfolioProfile.objects.filter(is_active=True).first()` (:28-30). No caching around any of them.
- All three are registered globally in `TEMPLATES[...]["context_processors"]` (django/config/settings.py:78-81), so they run for every view using `render()`, including Django admin pages.
- Error pages: custom `handler404`/`handler500` (django/config/urls.py:33-34) call `render(request, ...)` (django/main/views.py:88-96), so the processors run there too. On a 500 caused by a DB outage, these queries can raise again inside the handler (minor side effect, not claimed by the finding).
- No `CACHES` setting and no `django.core.cache` usage anywhere (grep of django/ and settings.py). Nuance: "no CACHES configured" means Django's default per-process LocMemCache, not "no cache backend at all".

## Why severity stays low
Queries are trivial (COUNT on a small table, PK lookup, one filtered row). For a low-traffic portfolio this is ~1-3 ms per page. Real, but not a bug.

## Better proposal (smaller)
- Do not cache `visitor_count` (changes per session via django/main/middleware.py:15-16); the finding correctly leaves it out.
- Simplest option: skip, or cache only the profile. If done: `cache.get_or_set("portfolio_profile", ..., 300)` plus `cache.delete` in a `post_save`/`post_delete` signal on `PortfolioProfile` and `Project` to avoid stale admin edits.
- Default LocMemCache is enough for this (no settings change); if Redis is used, pick a DB index other than 0, which is the Celery broker (django/config/settings.py:205).
