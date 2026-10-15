# F-130 (reproduce): Periodic jobs listed incompletely in architecture.md and README

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:214-227` `CELERY_BEAT_SCHEDULE` has three entries: `refresh_portfolio_heatmap_cache_task` (`crontab(minute=0)`, hourly), `sync_project_markdowns_task` (`crontab(hour="*/2", minute=0)`), `check_disk_usage_task` (`crontab(hour=6, minute=0)`, daily). Task defined at `django/main/tasks.py:201-202`.
- `docs/architecture.md:145-146` points to `CELERY_BEAT_SCHEDULE` and names only `sync_project_markdowns_task` as "Notable periodic job". Line 145 pointing to the schedule softens the gap: the wording does not claim the list is complete.
- `README.md:44` lists only scheduled markdown sync. README:45 mentions the heatmap snapshot but not its hourly refresh. README:75 mentions heatmap refresh and markdown sync in the admin panel description.
- `check_disk_usage_task` appears in neither README.md nor any `docs/*.md` (grep "disk" returns nothing).
- Small nit: the beat key `sync-project-markdowns-hourly` (settings.py:220) does not match its 2-hourly schedule. This is a naming issue, not a docs issue.

## Better proposal
In `docs/architecture.md:146`, replace the "Notable periodic job" line with a list of the three beat entries and their schedules (hourly, every 2 h, daily 06:00). Optionally add the daily disk-usage check to the README feature list. Effort: S.
