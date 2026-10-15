# F-078 (reproduce): TaskExecutionLog grows without bound, no index on ordering column

**Verdict:** CONFIRMED (the index part matters less than claimed)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `_log_task_execution` (django/main/tasks.py:260-271) only does `TaskExecutionLog.objects.create(...)`. It is called on every run: tasks.py:102 (markdown sync), :141/:167/:191 (heatmap refresh), :247 (disk check).
- Nothing in the repo deletes these rows. A grep over `*.py`, `*.sh`, `*.yml` and the Makefile finds no prune or delete code, and there is no `management/commands` directory.
- Beat schedule (django/config/settings.py:214-228): heatmap hourly (24/day), markdown every 2 h (12/day), disk daily (1/day), so 37 rows/day as the finding says. Manual admin triggers (views.py:429, :452) add more.
- `last_run_at` has no index (models.py:156). The model has no `Meta.indexes`, and only `task_name` has `db_index=True` (models.py:149). The about page (views.py:139, called only for admins) runs `order_by("-last_run_at", "-id")[:30]` (views.py:320).
- Scale check: about 13.5k small rows per year. PostgreSQL handles that with a seq scan and a top-N heapsort in a few ms, and only on admin page views. The missing index is not a real cost for years. The real issue is unbounded growth, and that is slow too. Low is the right severity.
- Unrelated note: `_schedule_next_heatmap_refresh` (views.py:189) has no callers. It is dead code and does not add log rows.

## Better proposal
Keep it to one line in `_log_task_execution`, after the create: delete rows whose `created_at` is older than 90 days (`created_at__lt=timezone.now() - timedelta(days=90)`). That needs no migration and the cost per run is trivial. Skip the index. Add it only if retention is dropped or the table grows past roughly 1M rows.
