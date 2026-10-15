# F-041 — Admin jobs panel hard-codes beat schedule, wrong next-run time, omits disk task

**Lens:** worth
**Verdict:** CONFIRMED (severity lowered)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/views.py:273-286` hard-codes labels, "Every 60 minutes"/"Every 2 hours" and `interval_minutes` 60/120, duplicating `CELERY_BEAT_SCHEDULE` (`django/config/settings.py:214-228`). Drift risk is real.
- `views.py:268-270` filters only heatmap + markdown task names; `check_disk_usage_task` (`settings.py:224-227`, writes `TaskExecutionStatus` at `django/main/tasks.py:206-247` under `main.check_disk_usage_task`) is not in the panel. Partly mitigated: free disk is shown separately via `_get_disk_info()` (`views.py:141`, `240`) and disk runs appear in the executed-tasks log (`views.py:318-320`).
- `views.py:292-296`: `next_run_at = last_run_at + interval` ignores crontab alignment (`crontab(minute=0)`, `crontab(hour="*/2", minute=0)`); never-run tasks get `now + interval`, which moves on every page load. Rendered at `django/main/templates/pages/about.html:166`.
- Worth doing: S effort, display-only, no contradicting decision in git log (panel dates from `7af03e4`, disk task added in `667e27f` without touching the panel).
- Why lowered to low: admin-only, display-only, no data or security impact; schedule changes are rare.

## Better proposal
Probe at HEAD (UTC, 05:52): `now + entry["schedule"].remaining_estimate(now)` returns 06:00 for all three crontab entries, which is correct.
- Use `now`, not `last_run_at`. It gives the next cron slot for never-run tasks too, so no "unknown" branch is needed, and a manual run does not skew it.
- Iterate `settings.CELERY_BEAT_SCHEDULE`. Keep one `{beat task path: label}` dict, because the status `task_name` (`main.check_disk_usage_task`, `tasks.py:19`) differs from the beat task path (`main.tasks.check_disk_usage_task`). Map the beat path to the status name with `.replace("main.tasks.", "main.")` or key the dict by status name.
- Derive `schedule_label` from `str(entry["schedule"])` or keep it in the same label dict. Do not keep `interval_minutes`.
