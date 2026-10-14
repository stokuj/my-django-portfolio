# arch-modules

Scope: module seams in `django/main` (views, heatmap/github_client, tasks, models, context_processors) at `dev` HEAD `4416049`.

## Findings

### 1. Task observability boilerplate repeated 4x
- Severity: medium | Category: simplification | Effort: S
- File: `django/main/tasks.py:31-102`, `113-191`, `206-247`, `260-271`
- Problem: every task does `get_or_create` + sets 8 status fields + `save(update_fields=[...same 8...])` + `_log_task_execution`. The 8-field list is copy-pasted 4 times; `sync_project_markdowns_task` also duplicates the `failed_results`/`last_error` join in two branches (72-89). Adding a field to `TaskExecutionStatus` means editing 5 places.
- Proposal: one helper in `tasks.py`: `_record_run(task_name, started_at, status, total, updated, failed, error="")` that sets `last_success_at`/`last_failure_at` from `status`, saves, and appends the `TaskExecutionLog` row. Tasks shrink to computing counts + one call. Skip a decorator/context manager: result shapes differ per task, a plain function is enough.
- Risk: low; `test_tasks.py` asserts on status rows, not on internals, so it should pass unchanged.

### 2. Heatmap refresh workflow split across view and task; view knows 6 heatmap functions
- Severity: medium | Category: architecture | Effort: M
- File: `django/main/views.py:14-21`, `146-237`; `django/main/tasks.py:119-171`
- Problem: "check token -> fetch -> persist error or payload" is implemented twice (view on stale cache, task on schedule). The view imports six heatmap functions (shallow interface) and also owns heatmap domain logic: response serialization (`_build_heatmap_snapshot_response`) and `_calculate_last_30_days_total` (40 lines of defensive parsing of a payload that `heatmap.build_weeks_payload` itself produces, `heatmap.py:50-57` - the `contribution_count` fallback and `"T"` split at `views.py:224,231` can never trigger).
- Proposal: deepen `heatmap.py` to two entry points: `refresh_snapshot() -> (snapshot, error)` (token check + fetch + persist, used by both task and view) and `snapshot_to_dict(snapshot)` (includes the 30-day total, simplified to read `day["date"]`/`day["count"]`). View becomes ~10 lines; task uses `refresh_snapshot()` and only records status.
- Risk: `test_views.py:205-305` patch `main.views.fetch_heatmap_data` / `main.views.get_configured_github_token`; those patch targets must move to `main.heatmap.*`.

### 3. Admin "scheduled jobs" panel duplicates beat schedule and omits the disk task
- Severity: medium | Category: architecture | Effort: S
- File: `django/main/views.py:264-315` vs `django/config/settings.py:214-227`
- Problem: labels and `interval_minutes` (60/120) are hard-coded copies of `CELERY_BEAT_SCHEDULE`. `check_disk_usage_task` (scheduled daily, writes `TaskExecutionStatus` under `DISK_USAGE_TASK_NAME`, `tasks.py:19,206`) is missing from the panel. `next_run_at = last_run + interval` ignores crontab alignment (e.g. manual admin run at 10:17 shows next run 11:17, beat runs at 11:00).
- Proposal: iterate `settings.CELERY_BEAT_SCHEDULE`; compute next run with the entry's celery schedule (`schedule.remaining_estimate(last_run_at)`); keep only a small `{task_name: label}` dict. Disk task appears automatically.
- Risk: low; the tests compare schedule content at `test_views.py:~70`, adjust expectations.

### 4. Disk check implemented twice
- Severity: low | Category: simplification | Effort: S
- File: `django/main/views.py:240-261`, `django/main/tasks.py:202-233`
- Problem: `shutil.disk_usage("/")` + critical/warning/ok classification lives in both modules; views imports `DISK_CRITICAL_GB`/`DISK_WARNING_GB` from tasks just to re-implement it. Thresholds could drift in logic (one already did: commit `d2b6257`).
- Proposal: single `disk_status()` in `tasks.py` returning the dict views.py builds today (incl. `level`); task maps `level` to status, view calls it. Drop the constant imports from views.
- Risk: none.

### 5. Dead self-rescheduling path for heatmap refresh
- Severity: low | Category: simplification | Effort: S
- File: `django/main/views.py:189-197`, `django/main/tasks.py:113,142,168,192,250-257`, `django/config/settings.py:218`
- Problem: `views._schedule_next_heatmap_refresh` has no callers. `schedule_next` is passed `False` by both beat and the admin view, so `_maybe_schedule_next_refresh` never enqueues anything; if it ever were `True` it would run in parallel with the hourly beat entry.
- Proposal: delete `_schedule_next_heatmap_refresh`, `_maybe_schedule_next_refresh`, the `schedule_next` parameter and the beat `kwargs`. Update `test_views.py:70,203`.
- Risk: messages already queued with `schedule_next=` kwarg would fail with TypeError; deploy with an empty queue or keep `**_kwargs` for one release.

### 6. handler500 runs DB-backed context processors
- Severity: low | Category: bug | Effort: S
- File: `django/main/views.py:95-97`, `django/main/context_processors.py:4-52`, `django/main/templates/errors/500.html:1`
- Problem: `render(request, "errors/500.html")` runs all three context processors (3 queries: `Project.count`, `PageView`, `PortfolioProfile`) and `500.html` extends `base.html`. When the 500 is caused by the DB being down, the error page raises again and the user gets Gunicorn's bare 500. Django's default `server_error` deliberately renders without a request context for this reason.
- Proposal: render the 500 template without request context (`loader.get_template(...).render()`), and ensure `base.html` tolerates missing profile vars (it already uses plain `{{ }}` lookups).
- Risk: 500 page loses profile/footer data; acceptable for an error page.

### 7. Unused override parameters and re-validation in heatmap
- Severity: low | Category: simplification | Effort: S
- File: `django/main/heatmap.py:68,77`, `111,121`, `83-86`
- Problem: `fetch_heatmap_data(github_token=None)` and `is_snapshot_stale(..., ttl_minutes=None)` overrides have no callers (code or tests). `heatmap.py:83-86` re-checks `login` that `github_client.fetch_authenticated_user` already guarantees (`github_client.py:72-77`).
- Proposal: drop both parameters and the redundant check.
- Risk: none.

## Rejected (would not pay off)
- Split `views.py` into a package (pages / admin_tools / api): 461 lines, 8 views. After findings 2-5 it drops to ~300 lines of mostly page views; a package adds files without leverage.
- Merge `heatmap.py` and `github_client.py`: the split is right. `github_client` is a clean adapter (HTTP + response validation, two exception types); `heatmap` is shaping + persistence. Tests already exercise each through its own interface.
- Route `markdown_sync.py` downloads through `github_client`: different hosts (raw.githubusercontent.com), no auth; one shared helper would be a hypothetical seam.
- Move markdown rendering/sanitizing (`views.py:33-87,340-377`) to its own module: single caller; move only when a second caller (e.g. admin preview) appears.
- Split `models.py` (262 lines, 7 small models) or derive `TaskExecutionStatus` from the latest `TaskExecutionLog` row: migration cost outweighs the saved double-write once finding 1 is done.
- Cache context processors: three indexed single-row queries per page on a portfolio site; caching adds invalidation logic for no measurable gain.
