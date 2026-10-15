# F-032 — Disk monitoring runs once a day and alerts nobody (worth lens)

**Verdict:** CONFIRMED (partially: the facts hold, but the severity and half of the proposal do not)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- Facts verified:
  - `django/config/settings.py:224-227`: `check-disk-usage-daily` runs at `crontab(hour=6, minute=0)`.
  - `django/main/tasks.py:202-249`: the task only logs (`logger.critical` at line 211, `logger.warning` at line 219) and writes `TaskExecutionStatus`.
  - `django/config/settings.py:183-200`: LOGGING has only a console `StreamHandler`. No `ADMINS`, `EMAIL_*`, `AdminEmailHandler` or Sentry is set up anywhere in settings or `.env.example`. So nobody is notified.
- The current behaviour was chosen on purpose:
  - `docs/superpowers/specs/2026-05-14-codebase-audit-design.md:36-40` specifies a daily task at 06:00 that shows its results on the admin about page.
  - `docs/superpowers/specs/2026-05-09-issue-57-disk-space-optimization-design.md:16` lists "Adding disk space monitoring or alerting" as a non-goal.
  - The finding does not acknowledge either decision.
- The impact is smaller than the finding states:
  - `django/main/views.py:141,240-241`: the about page reads `shutil.disk_usage("/")` live for staff, so the admin view is never a day old.
  - Issue #57 (commit `1b830b4`) already added log rotation and image/cache pruning, which removes the main sources of disk growth.
  - On a single-owner portfolio droplet, the remaining risk is a slow fill that nobody notices. That is low severity, not medium.
- Proposal:
  - The DigitalOcean Monitoring alert policy is the right fix. It needs zero code, uses a built-in platform feature, and is independent of whether Celery is healthy. An in-app alert cannot fire when the worker, beat or Redis is down, and a full disk can cause exactly that.
  - "Run the task hourly" is not worth doing. Without a notification channel it only refreshes a status row that nobody watches, and the about page is already live.

## Better proposal
- Enable a DO Monitoring alert (disk utilization > 85%, email) in the DO console. Leave the code as it is.
- Optionally, add one line to the issue-57 spec or the ops docs saying that alerting lives in DO Monitoring.
- Drop the hourly-schedule part. Do not add ADMINS/SMTP for this purpose.
