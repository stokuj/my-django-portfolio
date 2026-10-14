# cr-views-models

Scope: correctness review at HEAD (dev) of `django/main/{views,models,urls,admin,context_processors}.py` and `django/config/urls.py`.

## 1. Public heatmap endpoint refetches GitHub synchronously on every request while upstream fails
- Severity: medium | Category: performance | Effort: S
- Location: django/main/views.py:155-166 (with django/main/heatmap.py:159-171)
- Problem: `/about/heatmap-data/` is anonymous. When the snapshot is stale it calls `fetch_heatmap_data()` inline (two GitHub calls, timeouts 15s + 20s in github_client.py:55,121). On error, `update_snapshot_error` only writes `last_error` and never touches `fetched_at`, so the snapshot stays stale and every following visitor triggers another synchronous fetch. No lock, so concurrent visitors fetch in parallel. Result during a GitHub outage or bad token: Gunicorn workers blocked for up to ~35s per request and the token's rate limit burned by anonymous traffic. The hourly beat task already refreshes the same snapshot.
- Proposal: drop the inline fetch; serve the snapshot as-is (503 only when payload is empty) and let the beat task own refreshes. If freshness on first boot matters, enqueue `refresh_portfolio_heatmap_cache_task.delay()` instead of fetching inline.
- Risk: heatmap may be up to one beat interval old; first-ever load returns 503 until the task runs.

## 2. Custom 500 handler hits the DB, so it crashes when the error is a DB outage
- Severity: medium | Category: bug | Effort: S
- Location: django/main/views.py:95-97; django/main/context_processors.py:10,15,25; errors/500.html extends base.html
- Problem: `handler500` uses `render(request, ...)`, which runs all context processors (`Project.objects.count()`, `PageView` lookup, `PortfolioProfile` lookup). If the original exception is `OperationalError` (DB down), the handler raises again; each `convert_exception_to_response` layer retries the handler, so the DB is hit repeatedly and the user ends with Gunicorn's bare error page. Django's default 500 view renders with an empty Context for exactly this reason.
- Proposal: render `errors/500.html` without request context (`loader.get_template(...).render()` with no request) and make the template not depend on context-processor variables, or fall back to `django.views.defaults.server_error`.
- Risk: 500 page loses dynamic header data (site name, counts).

## 3. Old upload is deleted in pre_save, before the DB write commits
- Severity: medium | Category: bug | Effort: S
- Location: django/main/models.py:251-262 (also post_delete at 245-248)
- Problem: `_project_pre_save` deletes the previous thumbnail/markdown file before `save()` hits the DB. If the save or the surrounding transaction fails (admin change view is atomic and also saves M2M tags afterwards; `IntegrityError` on `blog_url`), the row rolls back but still points to a file that no longer exists. Same for `post_delete` inside a rolled-back transaction. Data loss of media files.
- Proposal: capture old names in pre_save, delete them in `post_save` via `transaction.on_commit(...)`; wrap the post_delete deletion in `transaction.on_commit` too.
- Risk: low; orphan file remains if the process dies between commit and callback.

## 4. Tag uppercasing happens after uniqueness validation, admin returns 500
- Severity: low | Category: bug | Effort: S
- Location: django/main/models.py:47-49
- Problem: `Tag.save()` uppercases `name`, but `ModelForm` runs `validate_unique()` on the raw value before save. Adding `python` in admin when `PYTHON` exists passes validation (case-sensitive lookup on Postgres) and then raises `IntegrityError` on save -> 500 instead of a form error.
- Proposal: normalize in `clean()` (`self.name = self.name.upper()`); `full_clean()` calls `clean()` before `validate_unique()`. Keep `save()` as is for non-form paths.
- Risk: none.

## 5. Duplicate URL name `home`; reverse resolves to `/home/`
- Severity: low | Category: bug | Effort: S
- Location: django/main/urls.py:5-6
- Problem: both `""` and `"home/"` are named `home`. Verified: `reverse("home")` returns `/home/`, so every `{% url 'home' %}` link and the redirect fallback in views.py:396 point to `/home/` while `/` serves identical content (duplicate URLs for SEO, inconsistent canonical).
- Proposal: keep `name="home"` only on `""`; make `home/` a `RedirectView` to `/` (or remove it).
- Risk: bookmarks to `/home/` keep working only if the redirect is kept.

## 6. Dead helper `_schedule_next_heatmap_refresh`
- Severity: low | Category: simplification | Effort: S
- Location: django/main/views.py:189-197
- Problem: defined but never called anywhere (grep across django/). It also swallows all exceptions silently.
- Proposal: delete it.
- Risk: none.

## 7. Admin job overview hardcodes beat intervals; "next run" is fabricated when never run
- Severity: low | Category: architecture | Effort: S
- Location: django/main/views.py:273-296
- Problem: intervals (60/120 min) duplicate `CELERY_BEAT_SCHEDULE` in settings and will drift silently if the schedule changes. When a task never ran, `next_run_at = now + interval` changes on every page load and shows a time that has nothing to do with the beat schedule.
- Proposal: derive interval from `settings.CELERY_BEAT_SCHEDULE[...]["schedule"]`; show `None`/"unknown" when `last_run_at` is missing.
- Risk: none.
