# F-032 (reproduce): Disk monitoring runs once a day and alerts nobody

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `django/config/settings.py:224-226`: beat entry `check-disk-usage-daily` uses `crontab(hour=6, minute=0)`, so it runs once a day.
- `django/main/tasks.py:202-245`: `check_disk_usage_task` only calls `logger.critical/warning/info` (lines 211, 219, 227) and saves a `TaskExecutionStatus` row plus `_log_task_execution`. It sends nothing else.
- `django/config/settings.py:183-201`: `LOGGING` has a single `console` StreamHandler. There is no `mail_admins` handler, and grep finds no `ADMINS`, `EMAIL_*`, Sentry or webhook anywhere in the repo. CRITICAL logs end up only in the worker container's stdout.
- The only place this is visible is `django/main/views.py:138-141`. The about page shows `disk_info` (live `shutil.disk_usage`) and task status, but only to an admin who opens it. That is pull, not push.
- `infra/` and `.github/` contain no monitoring or alerting.

Small nuance: the admin about page reads disk usage live (`views.py:240`), so the daily schedule only affects the stored status row. It does not limit what an admin sees on a visit. The core claim, that no one is notified, still holds.

Also, the thresholds are absolute: 1 GB critical and 2 GB warning (`tasks.py:20-21`). On a small droplet, a warning at 2 GB free can come too late for a log or image spike.

## Better proposal
Agree with the finding. The cheapest fix sits outside the code: a DigitalOcean Monitoring alert policy for disk utilization above 85%, sent by email. It has no code and no deps, and it works even when Celery is down. Once that exists, the daily task is redundant as an alert mechanism. Keep it only for the admin page, and don't add email or ADMINS plumbing just for this.
