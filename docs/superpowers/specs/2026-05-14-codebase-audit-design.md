# Codebase Audit — Design Spec

**Date:** 2026-05-14
**Branch:** `audit/codebase-2026`
**Approach:** One branch, one PR, categories as separate commits.

---

## Scope

Four audit categories, each producing immediate fixes:

1. Disk / Resources
2. Security
3. Dead code / Quality
4. Old packages / Upgrade

Plus one new feature: disk usage monitoring.

---

## Category 1 — Disk / Resources

### 1a. Disable Celery result backend writes

**Finding:** `CELERY_RESULT_BACKEND` is configured (redis:6379/1) but `AsyncResult` is never called anywhere in the codebase. Task results are written to Redis on every run and expire after the default 1-day TTL — wasted writes.

**Fix:** Add `CELERY_TASK_IGNORE_RESULT = True` to `django/config/settings.py`. Decorate `healthcheck_task` and all `@shared_task` functions with `ignore_result=True` explicitly. This stops Redis writes for task results entirely.

### 1b. Auto-delete media files on Project delete

**Finding:** When a `Project` is deleted (or its `thumbnail`/`markdown_file` field is cleared), the file on disk is not removed. `media/thumbnails/` and `media/blog_markdown/` grow without bound.

**Fix:** Add a `post_delete` signal handler on `Project` in `django/main/models.py` that calls `.delete(save=False)` on `thumbnail` and `markdown_file` if they exist. Also add a `pre_save` signal to detect field changes and delete the old file when a field is overwritten.

### 1c. Disk usage monitoring (new feature)

**New Celery beat task:** `check_disk_usage_task` runs daily at 06:00 UTC. Uses `shutil.disk_usage('/')` to check available bytes. Logs a `WARNING` if free space is below 2 GB, `CRITICAL` if below 1 GB. Stores result in `TaskExecutionStatus` using `task_name = "main.check_disk_usage_task"` — same pattern as existing tasks.

**About page admin panel:** Add a "Disk Usage" section visible to staff on `/about/`. Shows total, used, free (in GB) and a coloured badge (green / yellow / red). Data comes from `TaskExecutionStatus` for the disk task — no extra DB model needed.

---

## Category 2 — Security

### 2a. Restrict `img src` in markdown rendering

**Finding:** `ALLOWED_MARKDOWN_ATTRIBUTES` passes `img src` with any URL. Images from external domains load in the visitor's browser, leaking their IP (tracking pixels). While markdown content is controlled by the repo owner (GitHub README sync), the rendered HTML is still served to every visitor.

**Fix:** Replace the static `ALLOWED_MARKDOWN_ATTRIBUTES` dict with a custom bleach attribute cleaner function. The cleaner allows `img src` only when the URL starts with `https://github.com/` or `https://raw.githubusercontent.com/`. All other `img src` values are stripped. Other attributes keep their current rules.

Implementation in `django/main/views.py`:

```python
GITHUB_IMG_PREFIXES = (
    "https://github.com/",
    "https://raw.githubusercontent.com/",
    "https://camo.githubusercontent.com/",
)

def _clean_attributes(tag, name, value):
    if tag == "img" and name == "src":
        if not any(value.startswith(p) for p in GITHUB_IMG_PREFIXES):
            return False
    return True
```

Pass `_clean_attributes` as the `attributes` argument to `bleach.clean()`.

### 2b. `.env.example` warning comment

**Finding:** `.env.example` has `DJANGO_DEBUG=True` with no warning. A careless copy to production would expose debug info.

**Fix:** Add an inline comment: `DJANGO_DEBUG=True  # DEVELOPMENT ONLY — set to False in production`.

---

## Category 3 — Dead Code / Quality

### 3a. Remove `debug_task`

**Finding:** `django/config/celery.py` contains `debug_task` with `print(f"Request: {self.request!r}")`. It is never registered in `CELERY_BEAT_SCHEDULE`, never called from views or tests. Dead code with a `print()` in production module.

**Fix:** Delete the function entirely.

### 3b. Remove dead whitenoise comment

**Finding:** `django/config/settings.py` line 181 has a commented-out `STATICFILES_STORAGE = 'whitenoise...'` that was never used (Caddy serves static files). It creates confusion about which storage is active.

**Fix:** Remove the commented line. Keep only the active `StaticFilesStorage` line.

### 3c. Unify HTTP client — migrate `markdown_sync` to `requests`

**Finding:** `github_client.py` uses `requests`; `markdown_sync.py` uses `urllib` (stdlib). Two different HTTP stacks for the same job: fetching from GitHub.

**Fix:** Rewrite the URL fetch in `django/main/markdown_sync.py` using `requests.get()` with a consistent `timeout=15`. Remove `urllib.request`, `urllib.error` imports. Error handling maps `requests.HTTPError` / `requests.RequestException` to the same log paths as the current `HTTPError` / `URLError` handling. `requests` is already a declared dependency.

### 3d. Fix `visitor_counter` context processor

**Finding:** `visitor_counter` calls `PageView.get_instance()` which uses `get_or_create(id=1)` — a write-capable operation — on every request. This is unnecessary after the row exists.

**Fix:** Replace with a read-only query:
```python
def visitor_counter(request):
    instance = PageView.objects.filter(id=1).first()
    return {"visitor_count": instance.count if instance else 0}
```
The `get_instance()` class method is still used by the middleware (legitimate write path), so keep it on the model.

---

## Category 4 — Old Packages / Upgrade

### 4a. PostgreSQL 13 → 16

**Finding:** `postgres:13` is EOL November 2025 — no security patches. Current stable is 16 (supported to Nov 2028) or 17.

**Fix procedure (in-place major upgrade is not supported by Postgres Docker images):**

1. On the droplet (with stack running): `docker exec <db_container> pg_dump -U $DOCKER_DB_USER $DOCKER_DB_NAME > ~/pg_backup_$(date +%F).sql`
2. `make prod-down`
3. `docker volume rm my_django_portfolio_postgres_data`
4. Change `postgres:13` → `postgres:16` in `infra/docker-compose.prod.yml`
5. `make prod-up` — new Postgres 16 container initializes fresh
6. Wait for `db` healthy: `make prod-status`
7. `docker exec -i <db_container> psql -U $DOCKER_DB_USER $DOCKER_DB_NAME < ~/pg_backup_$(date +%F).sql`
8. Verify with `make prod-status` and spot-check the site.

The spec change is: update the image tag in `infra/docker-compose.prod.yml`. The migration procedure is documented in the implementation plan as a manual step.

### 4b. Python package patch updates

**Fix:** Run `uv lock --upgrade-package pillow --upgrade-package requests --upgrade-package bleach --upgrade-package django` to get latest patch releases within the current major versions. Commit updated `uv.lock`. Do not upgrade Django to 5.2 in this PR (separate decision — potential breaking changes).

### 4c. Node 20 → 22 in Dockerfile

**Finding:** `FROM node:20-slim` in `infra/Dockerfile`. Node 20 LTS EOL April 2026, Node 22 LTS EOL April 2027.

**Fix:** Single line change: `FROM node:22-slim`. No other changes required — the CSS build pipeline is Node-version-agnostic.

---

## Testing

Each category has clear verification:

| Category | Verification |
|---|---|
| 1a — ignore results | Check Redis db=1 stays empty after task run |
| 1b — file cleanup | Admin: delete a Project with thumbnail → check `media/thumbnails/` |
| 1c — disk monitoring | Run task manually via `manage.py shell`, check log output |
| 2a — img filter | Render markdown with external img → confirm stripped; github.com img → passes |
| 2b — env comment | Visual review |
| 3a — debug_task | `make verify` passes, no `debug_task` in codebase |
| 3b — whitenoise | `make verify` passes |
| 3c — urllib → requests | Markdown sync still works; no urllib imports in markdown_sync |
| 3d — visitor_counter | `make verify` passes; context processor returns count |
| 4a — postgres | Site works post-restore; `psql --version` shows 16.x |
| 4b — packages | `make verify` passes with new lock file |
| 4c — Node 22 | `make verify` builds CSS successfully |

Existing `make verify` suite catches regressions across all Python changes.

---

## Out of Scope

- Django 5.1 → 5.2 LTS upgrade (separate issue, potential breaking changes)
- Cache framework for context processors (over-engineered for portfolio traffic)
- GHCR old image cleanup (already handled by `docker image prune -af` in deploy workflow)
