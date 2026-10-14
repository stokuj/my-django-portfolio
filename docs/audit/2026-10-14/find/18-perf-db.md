# perf-db

Scope: ORM queries in views/context processors/middleware, model indexes, PageView/session/log growth, heatmap and markdown caching, Celery task efficiency, gunicorn settings (HEAD of `dev`).

## 1. Heatmap endpoint fetches GitHub synchronously inside the request
- Severity: high
- Category: performance
- File: django/main/views.py:157
- Problem: `about_heatmap_data` calls `fetch_heatmap_data()` inline whenever the snapshot is empty or stale. That is two blocking GitHub calls with timeouts of 15 s (`github_client.py:55`) and 20 s (GraphQL `requests.post`, timeout=20), so up to about 35 s, which is more than gunicorn's default 30 s worker timeout. On error, `update_snapshot_error` does not touch `fetched_at` (`heatmap.py:159-171`), so while GitHub is down or the token is bad, every visit to the about page repeats the fetch. There is no lock either, so concurrent visitors each fetch. The TTL (60 min, `settings.py:173`) matches the beat interval (`crontab(minute=0)`, `settings.py:217`), so any delay in beat hands the refresh to visitors.
- Proposal: Never fetch inline. Return the snapshot as it is (or 503 if there is none). If it is stale, call `refresh_portfolio_heatmap_cache_task.delay()` guarded by `cache.add("heatmap-refresh-lock", 1, 300)`. Alternatively set the TTL to about 2x the beat interval and let beat own refreshes.
- Effort: S
- Risk: The first-ever page load shows "no data" until the worker runs. That is acceptable because beat runs hourly.

## 2. Gunicorn runs with defaults: 1 sync worker, 30 s timeout
- Severity: high
- Category: ops
- File: infra/docker-compose.prod.yml:46
- Problem: `gunicorn config.wsgi:application --bind 0.0.0.0:8000` has no `--workers`/`--threads`/`--timeout`, and no `WEB_CONCURRENCY`/`GUNICORN_CMD_ARGS` is set anywhere. With one sync worker, a single slow request blocks the whole site, for example finding 1 or a slow client on a large page. A timeout kill returns 502 to everyone queued.
- Proposal: Set `--workers 2 --threads 4 --timeout 60` (or `GUNICORN_CMD_ARGS` in `.env`). Size workers to the droplet's RAM.
- Effort: S
- Risk: More workers use more RAM and more Postgres connections. Check the droplet's memory.

## 3. Markdown sync rewrites and renames every file on every run
- Severity: medium
- Category: performance
- File: django/main/markdown_sync.py:170
- Problem: `project.markdown_file.save(target_basename, ...)` reuses the current basename while the old file still exists, so the default `FileSystemStorage` appends a random suffix. Verified: `foo.md -> foo_puaSxJA.md -> foo_puaSxJA_cSyWW7L.md -> ...`, which grows until it hits the 100-char FileField limit. `project.save()` then triggers the `pre_save` signal (`models.py:251-262`), which does an extra SELECT and deletes the old file. This happens every 2 h for every blog project, even when the README did not change. The result is constant disk writes, DB writes and file-name churn.
- Proposal: Compare the downloaded text with the current file content (or a hash) and skip with `"reason": "unchanged"` when they match. When it changed, delete the old name first or save to a fixed name `f"{blog_url}.md"`.
- Effort: S
- Risk: The task's `updated` counts change meaning ("unchanged" must not be counted as failed). Adjust the status logic in `tasks.py:229-260`.

## 4. Anonymous home visits create DB session rows that are never purged
- Severity: medium
- Category: ops
- File: django/main/middleware.py:13
- Problem: `request.session["has_visited"] = True` makes a new `django_session` row for every cookieless client that hits `/` (crawlers, bots, uptime checks). The session engine is the default DB backend (no `SESSION_ENGINE` in settings), and nothing runs `clearsessions` (no beat entry, no cron). The table grows forever. It also adds `Set-Cookie`/`Vary: Cookie` to the home page, which prevents caching it.
- Proposal: Use a plain signed cookie (`response.set_cookie("visited", "1", max_age=...)`) instead of the session, or switch to `SESSION_ENGINE = "django.contrib.sessions.backends.cache"` with Redis. At minimum, add a daily beat task that calls `call_command("clearsessions")`.
- Effort: S
- Risk: With a cookie, the counter semantics change slightly. Admin login is unaffected if only the visitor flag moves.

## 5. No persistent DB connections (CONN_MAX_AGE = 0)
- Severity: medium
- Category: performance
- File: django/config/settings.py:109
- Problem: `DATABASES["default"]` sets no `CONN_MAX_AGE`, so every request opens and closes a new Postgres connection (TCP and auth) to run about 3-6 small queries.
- Proposal: Add `"CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60), "CONN_HEALTH_CHECKS": True`.
- Effort: S
- Risk: Persistent connections are held per worker thread. Keep workers x threads below Postgres `max_connections`.

## 6. Three uncached queries per template render in context processors
- Severity: low
- Category: performance
- File: django/main/context_processors.py:10
- Problem: `Project.objects.count()` (line 10), `PageView ... first()` (line 15) and `PortfolioProfile ... first()` (line 29) run on every `render()`. That includes admin pages, 404/500 pages and the about page. The values change rarely.
- Proposal: Cache the profile and project count with `cache.get_or_set(..., 300)` and invalidate on save (or just use the TTL). Keep the visitor count live or cache it for 60 s. Configure `CACHES` with the existing Redis (none is configured, so the default is per-process LocMem).
- Effort: S
- Risk: Admin edits to the profile show up after a TTL delay unless invalidated.

## 7. Blog markdown is re-read and re-rendered on every request
- Severity: low
- Category: performance
- File: django/main/views.py:402
- Problem: `blog_detail` reads the file from disk, runs `markdown.markdown` with extensions and `bleach.clean` on every view, although content changes at most every 2 h. Line 406 `Project.objects.order_by("-date")` also loads every column, including JSON fields, just for the sidebar titles and links.
- Proposal: `cache.get_or_set(f"md:{project.markdown_file.name}", lambda: _render_markdown_to_html(...), 86400)`. The file name changes on every sync (finding 3), so it doubles as the cache key. Use `.only("id", "title", "blog", "blog_url", "github_url")` for the sidebar.
- Effort: S
- Risk: If finding 3 is fixed with a fixed filename, the key must include a content hash or mtime.

## 8. TaskExecutionLog has no retention and no index on the ordering column
- Severity: low
- Category: performance
- File: django/main/views.py:320
- Problem: About 37 rows/day are appended (hourly heatmap, 2-hourly markdown, daily disk; `tasks.py:261`) with no pruning. The admin panel sorts by `-last_run_at`, which has no index (`models.py:156`), so it sorts the full table on each admin view of about. The table is small today but unbounded.
- Proposal: In `_log_task_execution`, delete rows older than N days (or keep the last 500). That makes the index unnecessary.
- Effort: S
- Risk: Old history is lost. That is fine for an ops panel.

## 9. Dead self-rescheduling heatmap code
- Severity: low
- Category: simplification
- File: django/main/views.py:189
- Problem: `_schedule_next_heatmap_refresh` is never called. `schedule_next=True` is never passed by beat (`settings.py:218`) or by views, so `_maybe_schedule_next_refresh` (`tasks.py:250-257`) is dead too. Beat already schedules the refresh hourly.
- Proposal: Delete both helpers and the `schedule_next` kwarg.
- Effort: S
- Risk: None; update the tests that pass `schedule_next`.

## 10. Redundant queries in visitor middleware and heatmap snapshot updates
- Severity: low
- Category: performance
- File: django/main/middleware.py:10
- Problem: The middleware runs `get_or_create(id=1)` (SELECT) and then a separate UPDATE. `update_snapshot_with_payload` and `update_snapshot_error` (`heatmap.py:139,168`) call `get_or_create_snapshot()` again even though the caller just loaded the snapshot (`views.py:155`).
- Proposal: In the middleware, run `if not PageView.objects.filter(id=1).update(count=F("count")+1): PageView.objects.create(id=1, count=1)`. Pass the snapshot into the update helpers, or use `HeatmapSnapshot.objects.filter(key="portfolio").update(...)`.
- Effort: S
- Risk: Minimal.

## Not an issue (checked)
- PageView is a single counter row (`models.py:106-115`), so it does not grow.
- `home` and `projects` use `prefetch_related("tags")` (`views.py:102,325`), which covers the `project.tags.all` loops in the templates. There is no N+1.
- `TaskExecutionStatus.task_name` is unique and therefore indexed. `HeatmapSnapshot.key` is unique. `Project.blog_url` lookup is covered by the partial unique constraint.
