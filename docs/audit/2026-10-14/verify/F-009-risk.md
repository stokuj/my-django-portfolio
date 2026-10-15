# F-009 (risk lens): Gunicorn runs with defaults: 1 sync worker, 30s timeout, no access log

**Verdict:** CONFIRMED (facts hold), severity overstated
**Confidence:** high
**Adjusted severity:** medium

## Verified facts
- `infra/docker-compose.prod.yml:46`: `gunicorn config.wsgi:application --bind 0.0.0.0:8000`. No flags, no `gunicorn.conf.py` in repo, no `WEB_CONCURRENCY`/`GUNICORN_CMD_ARGS` in `.env.example`. So: 1 sync worker, 30s timeout, accesslog off.
  - Caveat: `env_file: ../.env` (`:39-40`) means a prod-only `.env` could set `WEB_CONCURRENCY`/`GUNICORN_CMD_ARGS`; not verifiable from the repo.
- `infra/Caddyfile`: no `log` directive, so Caddy writes no access log either.
- Request-path slow call is real: `django/main/views.py:157-158` calls `fetch_heatmap_data()` synchronously when the snapshot is stale. That does REST (`django/main/github_client.py:55`, timeout 15s) + GraphQL (`github_client.py:121`, timeout 20s), worst case ~35s > gunicorn's 30s default, so the single worker can be killed mid-request.
- Staleness window is not rare by design: TTL default 60 min (`django/config/settings.py:173`) equals the beat interval (`settings.py:215-217`, `crontab(minute=0)`), so any delay in the hourly task, or a failed task, makes the next visitor trigger the inline fetch.

## Why severity is medium, not high
- Low-traffic personal portfolio; the blocking call is on the heatmap JSON XHR endpoint, not the page render, and only on a stale snapshot.
- No security exposure or data loss. It is availability degradation for a few seconds to ~35s.

## Risk of applying the proposed fix
- `--threads 4` switches to the `gthread` worker. Django and psycopg2 are thread-safe; no module-level mutable state found in `django/main/` (only a constant tuple at `views.py:70`). Low risk.
- Postgres connections: `CONN_MAX_AGE` is not set (`settings.py:109-118`), so connections close per request. 2x4 = at most 8 concurrent web connections plus Celery, well under Postgres's default 100. Low risk.
- RAM: about +1 Django process (~80-120 MB). The droplet also runs postgres, redis, the celery prefork worker, beat and caddy. Check `free -m` on the droplet before choosing `--workers 2`.
- `--timeout 60`: with gthread the timeout is a worker heartbeat, not a per-request limit. A hung GitHub call no longer kills the worker, it only uses up one thread. That is fine because the GitHub calls already have their own timeouts.
- `--access-logfile -`: goes to stdout, which is capped by the json-file driver (`docker-compose.prod.yml:70-74`, 10m x 3). No disk-fill risk. Query strings get logged (e.g. `?next=`), which is low sensitivity.
- No migration or compat impact. It is a one-line compose change, and rollback is reverting the line.

## Better proposal
1. Put the flags in the compose command so they are versioned, not in `.env`:
   `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 60 --access-logfile -`
2. The root cause of the blocking is F-005 (inline GitHub fetch in a request). If the stale path serves the old snapshot and enqueues the refresh, which `_schedule_next_heatmap_refresh` / the task already allows, the 30s risk goes away regardless of worker config. Fix F-005 first. F-009 is then cheap hardening.
3. Optional: set TTL slightly above the beat interval (e.g. 75 min) to close the TTL==beat race.
