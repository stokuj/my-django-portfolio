# F-041 - Admin jobs panel hard-codes beat schedule, wrong next-run time, omits disk task

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (display-only, admin-only panel)

## Reasoning
- `django/main/views.py:264-314` `_get_scheduled_jobs_overview()` hard-codes labels and `interval_minutes` 60/120 (`views.py:272-285`), duplicating `CELERY_BEAT_SCHEDULE` (`django/config/settings.py:214-228`). Nothing ties them together, so drift is possible.
- Only `REFRESH_HEATMAP_TASK_NAME` and `SYNC_MARKDOWNS_TASK_NAME` are queried (`views.py:268`). `check_disk_usage_task` is scheduled (`settings.py:224-227`) and writes `TaskExecutionStatus` under `DISK_USAGE_TASK_NAME` (`django/main/tasks.py:19,206`), but the panel never shows it.
- `next_run_at = last_run_at + interval` (`views.py:292-296`). The schedules are crontabs (`minute=0`, `hour="*/2", minute=0`), so the real next run is aligned to the clock. `last_run_at` is set at task start (`tasks.py:34`), and manual runs exist: `sync_project_markdowns_task.delay(...)` (`views.py:429`, including the single-blog `blog_slug` variant) and `refresh_portfolio_heatmap_cache_task.delay(...)` (`views.py:452`). A manual run at 10:30 shows a next run of 11:30 or 12:30, but beat fires at 11:00 or 12:00. For an odd-hour markdown run, the real next run comes 1 hour later, not 2.
- If the task never ran, the fallback `timezone.now() + interval` (`views.py:295`) shows a new time on every page load. It is not a real schedule.
- The output is rendered only in the admin section of `about.html:166` (via `views.py:139`). The impact is display-only, so medium overstates it.

## Better proposal
Keep a `{task_name: label}` dict. For each matching `CELERY_BEAT_SCHEDULE` entry, compute `next_run_at = now + entry["schedule"].remaining_estimate(now)`. For a crontab, the next fire time does not depend on the last run, so passing `now` gives the correct value even for a task that never ran, and no "unknown" branch is needed. Use `schedule_label` from a human string per entry, or drop it. Include the disk task.
