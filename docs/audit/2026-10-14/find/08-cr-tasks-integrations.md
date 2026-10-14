# cr-tasks-integrations

Scope: correctness review at HEAD (dev) of `django/main/tasks.py`, `heatmap.py`, `github_client.py`, `markdown_sync.py`, `django/config/celery.py`, and the `CELERY_*` settings (plus the view that consumes heatmap.py).

## 1. Markdown sync rewrites the file every run and the filename keeps growing
- Severity: high
- Category: bug
- Location: django/main/markdown_sync.py:168-172 (with models.py:261-262 pre_save delete)
- Problem: `target_basename = Path(old_name).name` reuses the current name. That file still exists, so `FileSystemStorage.get_available_name` appends `_XXXXXXX`. The pre_save signal then deletes the old file. Every 2-hourly run writes a new file, even when the README has not changed, and the name grows by 8 chars each time until it hits the 100-char `max_length`. After that the root is truncated and only the suffix changes. I reproduced this with Django 5.1.15 FileSystemStorage: `my-django-portfolio.md` became `my-django-portfolio_0ox8c2y_TSE22pJ_..._knlm2QI_bFxNyPt.md` (100 chars) after 8 runs. A request that loaded the Project before the swap reads a file that has been deleted, so `_load_project_markdown` returns None and the blog page is blank.
- Proposal: Skip the save when the content equals the existing file. Otherwise, write to a fixed name `f"{blog_url}.md"` and overwrite in place (delete before saving, or use a storage with overwrite enabled).
- Effort: S
- Risk: Low. A test should assert a stable name across two syncs.

## 2. Public heatmap endpoint calls GitHub synchronously, with no backoff on errors
- Severity: medium
- Category: security
- Location: django/main/views.py:157-166; django/main/heatmap.py:121-126; django/config/settings.py:173,217
- Problem: The anonymous GET `/about/heatmap-data/` calls `fetch_heatmap_data()` (REST 15s timeout + GraphQL 20s timeout) whenever the snapshot is stale. On error, only `last_error` is written and `fetched_at` stays old, so the snapshot stays stale. While GitHub is slow or down, or the token has expired, every visitor request makes fresh GitHub calls and can hold a Gunicorn worker for up to ~35s. Nothing rate-limits this. The TTL (60 min) also equals the beat period (hourly at :00), so a visitor can win the race against beat at every expiry.
- Proposal: Serve the snapshot only and let beat refresh it (the task already exists). Alternatively, record the time of the last attempt and do not retry within the TTL. In either case, set the TTL above the beat interval.
- Effort: S
- Risk: The first page load after a fresh deploy shows nothing until the first beat run or a manual refresh.

## 3. `last_success_at` is cleared on every failure
- Severity: low
- Category: bug
- Location: django/main/tasks.py:74,84,123,149,216,224
- Problem: The failure and partial-success branches set `last_success_at = None`, so the about page (about.html:225) loses the time of the last successful run, which is what an operator wants to see.
- Proposal: Leave `last_success_at` unchanged on failure. Do the same for `last_failure_at` on success.
- Effort: S
- Risk: Tests that assert None need updating.

## 4. Dead self-rescheduling chain (`schedule_next`)
- Severity: low
- Category: simplification
- Location: django/main/tasks.py:113,142,168,192,250-257; django/main/views.py:189-198; django/config/settings.py:218
- Problem: Every caller passes `schedule_next=False` (beat kwargs and views.py:452). `views._schedule_next_heatmap_refresh` has no callers. If someone enabled it, it would duplicate the hourly beat entry.
- Proposal: Remove the `schedule_next` param, `_maybe_schedule_next_refresh`, `_schedule_next_heatmap_refresh`, and the beat kwargs.
- Effort: S
- Risk: Tests that reference the param need updating.

## 5. Status bookkeeping is copy-pasted six times
- Severity: low
- Category: simplification
- Location: django/main/tasks.py:63-101,119-141,146-167,172-191,206-247
- Problem: The same 8-field `update_fields` list and success/failure assignments are repeated in every branch, so a new field has to be added in six places.
- Proposal: Add one helper `_record(status, ok, total, updated, error)` that sets the fields, saves, and logs.
- Effort: S
- Risk: Low; covered by test_tasks.py.

## 6. Redundant exception handling around requests
- Severity: low
- Category: simplification
- Location: django/main/markdown_sync.py:107-110,154-155; django/main/github_client.py:57,123
- Problem: `requests.RequestException` already subclasses `OSError`, and `Timeout` subclasses `RequestException`. Wrapping it into `OSError` and catching `(HTTPError, RequestException, UnicodeDecodeError, ValueError, OSError)` is equivalent to catching `(OSError, ValueError)`.
- Proposal: Drop the re-wrap and shrink the tuples.
- Effort: S
- Risk: None.

## 7. `TaskExecutionLog` grows without bound
- Severity: low
- Category: ops
- Location: django/main/tasks.py:260-271
- Problem: About 37 rows/day (24 heatmap, 12 markdown, 1 disk), about 13.5k/year. Nothing prunes them, and views.py:320 only reads the last 30.
- Proposal: Delete rows older than N days inside `_log_task_execution`, or in the daily disk task.
- Effort: S
- Risk: Loses old history (intended).

## 8. Single-slug or empty runs overwrite the global markdown status as SUCCESS
- Severity: low
- Category: bug
- Location: django/main/tasks.py:36-71
- Problem: A manual run for one slug, or a slug with no match (total 0), writes SUCCESS to the single `main.sync_project_markdowns_task` status row. This hides failures for other projects from the previous full run.
- Proposal: Do not update the status row when `blog_slug` is set, or treat total 0 as a failure.
- Effort: S
- Risk: Low.

## 9. Result backend configured but every result is ignored
- Severity: low
- Category: simplification
- Location: django/config/settings.py:207,210,213
- Problem: `CELERY_TASK_IGNORE_RESULT=True` and every task has `ignore_result=True`. Views only use `async_result.id`, which exists without a backend.
- Proposal: Remove `CELERY_RESULT_BACKEND` and `CELERY_RESULT_SERIALIZER`.
- Effort: S
- Risk: None unless someone later polls results.

## 10. Beat entry name does not match its schedule
- Severity: low
- Category: docs
- Location: django/config/settings.py:220-222
- Problem: `sync-project-markdowns-hourly` runs `crontab(hour="*/2")`, every 2 hours.
- Proposal: Rename it to `sync-project-markdowns-2h`. The beat schedule DB re-keys automatically.
- Effort: S
- Risk: None.
