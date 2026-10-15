# F-009 (worth) — Gunicorn runs with defaults: 1 sync worker, 30s timeout, no access log

**Verdict:** CONFIRMED (severity lowered)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `infra/docker-compose.prod.yml:46`: `gunicorn config.wsgi:application --bind 0.0.0.0:8000` with no flags. There is no `gunicorn.conf.py` in the repo, and no `WEB_CONCURRENCY` or `GUNICORN_CMD_ARGS` in `.env.example` or the compose env (`:52-64`). Gunicorn 23 (`pyproject.toml:12`) therefore runs 1 sync worker, a 30s timeout and no access log.
- `infra/Caddyfile` has no `log` directive, so Caddy writes no access log either.
- The blocking risk is real. `about_heatmap_data` (`django/main/views.py:156-158`) calls GitHub synchronously when the snapshot is stale. That makes two sequential requests with timeouts of 15s and 20s (`django/main/github_client.py:55`, `:121`), up to 35s in the worst case. That is longer than gunicorn's 30s timeout: the worker is killed and the client gets a 502. While the request runs, the single worker serves nobody else. TTL (`settings.py:173`, 60 min) equals the beat interval (1h), so the stale path can also be hit when beat is working normally.
- The proposed risks are small. `CONN_MAX_AGE` is not set (default 0, so no persistent connections), and the extra Postgres connections stay at 8 or fewer. Stdout logs from `web` are already rotated (`docker-compose.prod.yml:70-74`, json-file, 10m x 3), so an access log on stdout is bounded.
- No doc or commit makes the defaults a deliberate choice (`git log --grep=gunicorn` shows only `7cfc199 add gunicorn`).
- Why not high: this is a low-traffic portfolio, and the slow path runs about once an hour. It is an availability and observability gap, not data loss or a security issue. The root cause of the 35s request is F-005 (a synchronous fetch in the request path), not the gunicorn tuning.

## Better proposal
Keep the smallest diff: add flags to the existing command at `docker-compose.prod.yml:46`, with no new config file.
`gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --access-logfile -`
- `--threads > 1` switches gunicorn to gthread on its own, so no `--worker-class` is needed.
- Use `--timeout 45` only if F-005 is not fixed, because 60 hides hangs. Once F-005 moves the fetch off the request path, keep the 30s default.
- Leave Caddy logging alone, because the gunicorn access log covers it.
