# F-072 - TaskExecutionStatus duplicates the latest TaskExecutionLog row

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (unchanged)

## Reasoning

- Same fields: `TaskExecutionStatus` (django/main/models.py:130-140) has `task_name` + 8 `last_*` columns. `TaskExecutionLog` (django/main/models.py:149-162) has the same 9 columns plus `created_at`. Log even reuses `TaskExecutionStatus.STATUS_CHOICES` (models.py:152).
- Every write path sets all 8 `last_*` fields on the status row, saves it, then calls `_log_task_execution(status)`, which copies the same 9 fields into a new log row (django/main/tasks.py:260-271):
  - markdown sync: tasks.py:31-102
  - heatmap refresh, all three branches: tasks.py:114-135, 147-167, 171-187
  - disk usage: tasks.py:206-243
- No carried-over state: `last_success_at` / `last_failure_at` are not "last ever" timestamps; each run overwrites them with `now()` or `None` (e.g. tasks.py:69-70, 74-75, 123-124, 213-214). So the status row equals the newest log row field-for-field.
- No other writers: admin makes all status fields read-only (django/main/admin.py:75-85); no code deletes or prunes logs (only `create` at tasks.py:261 and read at views.py:320).
- Only reader of status data: `_get_scheduled_jobs_overview` (django/main/views.py:265-271), for 2 task names. Replaceable by latest log per task_name.
- Minor edge: an admin could delete log rows by hand (delete not disabled in admin.py:89-110), after which the status row would outlive its log. Not a real reason to keep the model.

## Better proposal

Same direction, plus:
- Read latest log per task in views.py:265-271, e.g. `TaskExecutionLog.objects.filter(task_name__in=[...]).order_by("task_name", "-last_run_at", "-id").distinct("task_name")` (Postgres) or one `.filter(task_name=n).order_by("-last_run_at","-id").first()` per name (only 2 names).
- Build the log row directly in tasks (drop the status `get_or_create` + `save(update_fields=...)` blocks repeated 5 times).
- `last_success_at` / `last_failure_at` carry no info beyond `last_status` + `last_run_at`; drop them in the same migration.
- Effort M holds: migration, admin, and many assertions in django/main/tests/test_tasks.py and test_models.py:232-245 read `TaskExecutionStatus`.
