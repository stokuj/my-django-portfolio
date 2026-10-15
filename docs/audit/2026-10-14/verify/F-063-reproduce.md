# F-063 — Beat entry 'sync-project-markdowns-hourly' runs every 2h

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning

- `django/config/settings.py:220` defines key `"sync-project-markdowns-hourly"`.
- `django/config/settings.py:222` sets `"schedule": crontab(hour="*/2", minute=0)`, i.e. every 2 hours at :00. The name is misleading exactly as described.
- CLAUDE.md already documents "Markdown sync: every 2 hours", so only the key name is wrong.
- No code or test references this key by name (grep over `django/`, only `refresh-portfolio-heatmap-hourly` is looked up at `django/main/tests/test_views.py:64`). Rename is safe.
- Beat uses Celery's default PersistentScheduler with a shelve file on a volume (`infra/docker-compose.prod.yml:128`); no django_celery_beat. On startup the scheduler merges the configured schedule into the shelve and drops keys missing from config, so a rename leaves no stale entry. Expect at most one extra or skipped run after the deploy.

## Better proposal

Same as proposed: rename to `sync-project-markdowns-every-2h` (one line, effort S). Do not change the cadence.
