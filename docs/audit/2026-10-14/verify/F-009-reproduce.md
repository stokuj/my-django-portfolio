# F-009 - Gunicorn runs with defaults: 1 sync worker, 30s timeout, no access log

**Verdict:** CONFIRMED (facts), severity overstated
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `infra/docker-compose.prod.yml:46` runs `gunicorn config.wsgi:application --bind 0.0.0.0:8000` with no `--workers`, `--threads`, `--timeout`, `--access-logfile`.
- No `gunicorn.conf.py` / `gunicorn*.py` in the repo; `infra/Dockerfile` has no CMD/ENV for gunicorn; `WEB_CONCURRENCY` and `GUNICORN_CMD_ARGS` appear nowhere in the repo (incl. local `.env`, `.env.example`). The droplet's real `.env` (loaded via `env_file`, `docker-compose.prod.yml:39-40`) cannot be checked from here.
- gunicorn 23.0.0 (`pyproject.toml:12`) defaults: 1 sync worker, 30s timeout, access log disabled. So a single request at a time.
- Slow path is real: `django/main/views.py:156-157` calls `fetch_heatmap_data()` synchronously when the snapshot is empty or stale; it does two GitHub calls with `timeout=15` and `timeout=20` (`django/main/github_client.py:55,121`). Worst case 35s > 30s worker timeout, so the worker is killed (502) and all requests queue behind it meanwhile.
- Mitigation that reduces likelihood: Celery beat refreshes the snapshot hourly, so the in-request fetch only runs on cold start or when beat/worker lag behind the TTL.
- Caddy: `infra/Caddyfile:16-30` has no `log` directive, so no access log. Correct.

## Why medium, not high
Low-traffic personal portfolio; not exploitable, no data loss. Impact is latency/502s under concurrent load or a slow GitHub API, plus missing access logs for ops.

## Better proposal
Add `--workers 2 --threads 4 --timeout 60 --access-logfile -` to `docker-compose.prod.yml:46` (threads cover I/O-bound GitHub calls cheaply; DB connections = workers*threads, fine for Postgres default 100). Optionally add `log` to the Caddy site block instead of gunicorn access log - one is enough. Longer term, drop the synchronous fetch in `about_heatmap_data` and rely on the Celery task (see F-005).
