# sec-endpoints

Scope: `django/main/urls.py`, `django/main/views.py`, `django/main/middleware.py` (+ `heatmap.py`, `github_client.py`, settings, prod compose as needed) at HEAD of `dev`.

Checked, no issue found:
- Admin-tools endpoints (`views.py:422-461`): `@staff_member_required` + `@require_POST`, no `csrf_exempt` anywhere, `CsrfViewMiddleware` enabled (`settings.py:62`).
- Redirects use `url_has_allowed_host_and_scheme` with `request.get_host()` (`views.py:380-396`); external `next` rejection is tested (`tests/test_views.py:573`).
- `blog_slug` echoed into flash messages is autoescaped (`templates/base.html:95`).

## 1. Anonymous heatmap endpoint refetches GitHub on every request after any upstream error
- Severity: high
- Category: security
- File: `django/main/views.py:157`
- Problem: `about_heatmap_data` is public and does a synchronous GitHub fetch (REST `/user` + GraphQL, timeouts 15s + 20s, `github_client.py:55,121`) whenever the snapshot is empty or stale. On failure, `update_snapshot_error` (`heatmap.py:159-170`) only writes `last_error` and never advances `fetched_at`, so the snapshot stays stale and every subsequent request repeats the outbound fetch. No lock, no backoff, no rate limit. Prod runs gunicorn with defaults (`infra/docker-compose.prod.yml:46`: 1 sync worker, 30s timeout), so while GitHub is slow/down or the token is expired, a simple `curl` loop on `/about/heatmap-data/` pins the only worker (worst case 35s > 30s worker timeout) and takes down the whole site; it also burns the token's GitHub rate limit shared with the Celery refresh task.
- Proposal: stop fetching in the request path. Beat already refreshes hourly (`settings.py:215`): serve whatever snapshot exists, return 503 when none. If on-demand refresh is wanted, enqueue `refresh_portfolio_heatmap_cache_task` guarded by `cache.add("heatmap-refresh-lock", 1, 300)` instead of fetching inline. Minimum fix: record an attempt timestamp on error and skip refetch for N minutes. Add one test asserting a second request after an error does not call `fetch_heatmap_data`.
- Effort: S
- Risk: First page load after a fresh deploy shows "no data" until beat runs (or until an admin clicks "run heatmap refresh"). Existing tests `test_about_heatmap_data_fetches_sync_when_cache_missing` (`tests/test_views.py:242`) need updating.

## 2. Visitor middleware creates a DB session row per cookieless home hit; sessions never purged
- Severity: medium
- Category: ops
- File: `django/main/middleware.py:14`
- Problem: every request to `/` or `/home/` without a session cookie (bots, crawlers, curl) sets `request.session["has_visited"]`, which inserts a `django_session` row (default DB engine, no `SESSION_ENGINE` set) and runs an `UPDATE` on the counter. `clearsessions` is not scheduled anywhere (`CELERY_BEAT_SCHEDULE`, `settings.py:214-230`), so expired rows accumulate forever. A loop of cookieless GETs grows the table without bound and inflates the visitor count.
- Proposal: add a daily beat entry running `call_command("clearsessions")`. Optionally skip counting for requests without a `User-Agent` / obvious bots. Switching to `SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"` would remove DB writes entirely, but affects admin login sessions; do only if acceptable.
- Effort: S
- Risk: Low. `clearsessions` only deletes expired rows.

## 3. Dead helper `_schedule_next_heatmap_refresh` in views
- Severity: low
- Category: simplification
- File: `django/main/views.py:189`
- Problem: `_schedule_next_heatmap_refresh` is defined but never called (only its definition matches a repo-wide grep). Scheduling lives in `tasks._maybe_schedule_next_refresh`.
- Proposal: delete the function.
- Effort: S
- Risk: None.
