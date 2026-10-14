# mattpocock-standards

Scope: Standards axis of `mattpocock-skills:code-review` over the full tree at HEAD (`dev`, 4416049). Standards sources: CLAUDE.md, docs/architecture.md, docs/implementation.md, docs/frontend.md, pyproject ruff config, plus the Fowler smell baseline (judgement calls).

## 1. `make verify` / CI never runs the 96 Django tests
- Severity: high | Category: tests | Effort: S
- Location: Makefile:38 (also CLAUDE.md:11, CLAUDE.md:23)
- Problem: `uv run python django/manage.py test` with no label is run from the repo root, so DiscoverRunner discovers from `.`. `django/` has no `__init__.py`, so only `tests/` is found. Verified: `Ran 26 tests in 0.003s` (operational tests) vs `manage.py test main` -> `Ran 96 tests`. CI (`.github/workflows/django.yml:46`) runs `make verify`, so the Django tests are never run. CLAUDE.md says verify runs "Django tests".
- Proposal: Change Makefile:38 to `... django/manage.py test main` and add `uv run python -m unittest discover tests` as a separate step. Update the CLAUDE.md:23 command to match.
- Risk: Tests that have broken without anyone noticing may start failing in CI. That is the point of the fix, but it may block the next PR.

## 2. CLAUDE.md test commands are wrong (pytest not installed)
- Severity: medium | Category: docs | Effort: S
- Location: CLAUDE.md:23, CLAUDE.md:29
- Problem: `uv run python -m pytest tests/` fails because pytest is not a dependency (`ModuleNotFoundError: No module named 'pytest'`). `tests/` is plain `unittest`. CLAUDE.md:23 says the label-less command runs the Django app tests, but it runs only the 26 operational tests (see #1).
- Proposal: Replace it with `uv run python -m unittest discover tests` and use `manage.py test main` for the Django tests.
- Risk: none

## 3. CLAUDE.md names a CI workflow that does not exist
- Severity: low | Category: docs | Effort: S
- Location: CLAUDE.md:93
- Problem: The doc says `django-ci.yml` runs on PRs to main. The real file is `.github/workflows/django.yml`, and it runs on push and PR to `main`/`master` (django.yml:3-7).
- Proposal: Change the name and trigger description to match.
- Risk: none

## 4. The ruff config in pyproject is not enforced on application code
- Severity: medium | Category: ci | Effort: S
- Location: Makefile:39, pyproject.toml (`[tool.ruff.lint] select = ["E","F","I"]`), CLAUDE.md:34
- Problem: verify lints only `infra/scripts tests`. Running `ruff check django --exclude django/main/migrations` reports 31 violations: 15 I001, 11 E501, 3 F401 (e.g. django/main/tests/test_tasks.py:2 unused `shutil`, test_models.py:290,301), and 2 F841 (test_tasks.py:98,200 unused `second`). The documented lint standard does not cover the main codebase.
- Proposal: Lint `django` in verify (exclude migrations), run `ruff check --fix` once, and fix the E501/F841 cases by hand.
- Risk: The import reordering is a mechanical diff that touches many files.

## 5. View re-implements heatmap refresh and blocks the request on GitHub
- Severity: medium | Category: architecture | Effort: M
- Location: django/main/views.py:146-168, against docs/architecture.md:142 and :194
- Problem: architecture.md says "Keep views thin; move business logic into helpers/services/tasks" and "Celery is used for jobs that should not block HTTP requests". `about_heatmap_data` calls `fetch_heatmap_data()` (GitHub REST + GraphQL) synchronously when the snapshot is stale. It also repeats the fetch/update_snapshot_error/update_snapshot_with_payload sequence from `refresh_portfolio_heatmap_cache_task` (tasks.py:113-198). Possible Duplicated Code.
- Proposal: Have the view always serve the snapshot. When it is stale, enqueue `refresh_portfolio_heatmap_cache_task.delay()` (or call one shared `refresh_snapshot()` helper used by both). Otherwise update the doc to say the request path can block.
- Risk: The first visit with an empty snapshot would return no data until the worker runs.

## 6. Dead helper `_schedule_next_heatmap_refresh`
- Severity: low | Category: simplification | Effort: S
- Location: django/main/views.py:189-197
- Problem: Nothing calls it (grep finds only the definition). It also swallows all exceptions.
- Proposal: Delete it.
- Risk: none

## 7. Speculative `schedule_next` parameter
- Severity: low | Category: simplification | Effort: S
- Location: django/main/tasks.py:113, :250-257; django/config/settings.py:218; views.py:452
- Problem: Every caller passes `schedule_next=False` (beat kwargs, admin view). No code or test passes `True`, so `_maybe_schedule_next_refresh` is never used in practice, and beat already handles hourly scheduling. Possible Speculative Generality.
- Proposal: Remove the parameter, `_maybe_schedule_next_refresh`, and the beat `kwargs`. Update test_views.py:70 and :203.
- Risk: Tasks already queued with `schedule_next` kwargs would fail after deploy. Make sure the queue is empty first.

## 8. Status-save block copy-pasted across tasks
- Severity: low | Category: simplification | Effort: S
- Location: django/main/tasks.py:123-141, 147-167, 171-191, 238-248 (plus sync task ~:90)
- Problem: The same ~20-line "set last_* fields, save(update_fields=[8 fields]), _log_task_execution" block is repeated about 5 times. Possible Duplicated Code / Data Clumps.
- Proposal: Add one helper `_record(status, outcome, updated, failed, error="")` that sets the fields, saves, and logs.
- Risk: Low. test_tasks covers these paths once #1 is fixed.

## 9. Admin schedule overview duplicates CELERY_BEAT_SCHEDULE
- Severity: low | Category: architecture | Effort: S
- Location: django/main/views.py:264-286; django/config/settings.py:214-228
- Problem: The intervals ("Every 60 minutes" / 120) are hardcoded in the view separately from beat, so a schedule change needs edits in two files (possible Shotgun Surgery). The daily `check-disk-usage-daily` job is missing from the overview. The beat key `sync-project-markdowns-hourly` (settings.py:220) runs every 2 hours (possible Mysterious Name). `_get_disk_info` (views.py:240) also repeats the disk thresholds logic from `check_disk_usage_task` (tasks.py:202).
- Proposal: Rename the beat key and derive the labels/intervals from `settings.CELERY_BEAT_SCHEDULE`, or at least keep them next to it. Share one disk-level helper.
- Risk: none

## 10. Task docs out of sync with tasks.py
- Severity: low | Category: docs | Effort: S
- Location: docs/implementation.md:36; CLAUDE.md "Celery beat schedule" section; docs/architecture.md:146
- Problem: implementation.md describes `healthcheck_task` as a "worker health check", but no compose healthcheck or other code calls it (it is only referenced in test_tasks.py:337). `check_disk_usage_task` and its daily 06:00 beat entry (settings.py:224-227) are missing from implementation.md, architecture.md, and the CLAUDE.md beat schedule.
- Proposal: Document the disk-check task. Either wire `healthcheck_task` into a worker healthcheck or delete it and its doc line.
- Risk: none

## 11. Non-English comments and leftover debug code
- Severity: low | Category: docs | Effort: S
- Location: django/config/settings.py:25, :28, :119-121; django/main/views.py:327
- Problem: The global CLAUDE.md rule says code comments must be in English. These comments are in Polish ("ustaw domyślne typy i wartości", "wskazujemy ścieżkę do .env", "Pobieramy wszystkie unikalne tagi"). settings.py:119-121 still has commented-out `print` debugging. `environ.Env(DEBUG=(bool, False))` (settings.py:24-27) declares a scheme for `DEBUG` that is never read, because DEBUG comes from `DJANGO_DEBUG`.
- Proposal: Translate or drop the comments, remove the commented prints, and use plain `environ.Env()`.
- Risk: none
