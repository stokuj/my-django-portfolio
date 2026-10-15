# F-048 (reproduce lens): No healthchecks; startup ordering by sleep and an endless wait-for-db loop

**Verdict:** CONFIRMED (not refuted)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning (verified at HEAD)

Every factual claim matches the code:

- No `healthcheck:` key in either compose file. `depends_on` is a plain list with no `condition:` (prod.yml:65-67, 104-107, 142-144, 170-171; dev.yml:52, 86, 119).
- web uses `entrypoint: sh /app/django/entrypoints/wait-for-db.sh` (prod.yml:42, dev.yml:31). The script loops `until psql ... -c '\q'; do sleep 1; done` with no retry limit (wait-for-db.sh:15-18). Any persistent failure (wrong password, missing DB) loops forever. README.md:163 already documents this ("web can stay in wait-for-db").
- worker starts with `sleep ${WORKER_START_DELAY_SECONDS:-45}` (prod.yml:87, dev.yml:69, .env.example:47).
- beat has no wait (prod.yml:126, dev.yml:103).
- `chmod +x` (Dockerfile:30) has no effect because the script is run as `sh <script>`, never executed directly.
- `healthcheck_task` (tasks.py:24-26) is referenced only by a test (test_tasks.py:14, 337) and docs/implementation.md:36. Nothing calls it.

## Why severity drops to low

- There is no data loss and nothing exploitable. The endless loop happens only when the config is wrong, and it is easy to diagnose: psql stderr is not suppressed, so "password authentication failed" shows in the logs every second.
- Celery worker and beat retry the broker connection on their own, and beat's file scheduler does not need the DB at startup. In practice, the missing wait on beat does no harm.
- The `sleep 45` is a crude way to wait for `migrate`, but it works. This is cleanup and robustness work, not a real bug.

## Extra observation

- In prod, `web` has no `restart:` policy (prod.yml:33-74), while db, redis, worker and beat use `restart: always`. If wait-for-db is removed, a failed migrate leaves web stopped until someone intervenes. That is still better than looping without end, but add `restart: always` to web as part of the same change.

## Better proposal

Keep the proposal, with these adjustments:
1. db: `healthcheck: test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U $$POSTGRES_USER -d $$POSTGRES_DB"]`. Use `-h 127.0.0.1` so that the socket-only temporary server during first-boot init is not reported as ready.
2. redis: `redis-cli ping`. web: `python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"`. This works only while `127.0.0.1` is in ALLOWED_HOSTS (settings.py:43 default; prod `.env` must keep it). Otherwise Django returns 400 and the check fails.
3. web `depends_on: db: {condition: service_healthy}, redis: {condition: service_healthy}`. worker/beat `depends_on: web: {condition: service_healthy}`, which replaces the sleep and `WORKER_START_DELAY_SECONDS`.
4. Add `restart: always` to prod web.
5. Then delete wait-for-db.sh, the `entrypoint:` lines, Dockerfile:30 chmod, `postgresql-client` (Dockerfile:17), and the README.md:163 note.
6. Separately, either delete `healthcheck_task` and its test, or use it as a worker healthcheck (`celery -A config inspect ping` is simpler and needs no task).
