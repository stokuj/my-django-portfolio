# F-048 — No healthchecks; startup ordering by sleep and an endless wait-for-db loop

**Verdict:** CONFIRMED (facts hold), but the proposal is partly wrong. See the better proposal below.
**Confidence:** high
**Adjusted severity:** low (was medium)

## Facts verified at HEAD
- No `healthcheck:` on any service. Every `depends_on` is a plain list: infra/docker-compose.prod.yml:65-67, 104-107, 142-144, 170-171; infra/docker-compose.dev.yml:52-54, 86-89, 119-121.
- django/entrypoints/wait-for-db.sh:15-18 runs `until psql ...; sleep 1` with no limit, so a wrong password or a missing DB loops forever. README.md:163 already documents this ("`web` can stay in `wait-for-db`").
- Worker `sleep ${WORKER_START_DELAY_SECONDS:-45}`: prod.yml:87, dev.yml:69, .env.example:47. This was a deliberate workaround (commit 4c643b5 "Add delay for worker startup", meant to let web/db/redis stabilize), not an accident.
- Beat has no wait (prod.yml:126). It only needs the broker, and Celery retries the broker connection while `restart: always` covers the rest, so this is not a real problem.
- Dockerfile:30 `chmod +x` has no effect, because the entrypoint is invoked as `sh <path>` (prod.yml:42, dev.yml:31).
- tasks.py:24-26 `healthcheck_task` is never invoked. It is tested (test_tasks.py:337) and documented (docs/implementation.md:36), so it is out of scope here.
- Deploy runs `up -d --force-recreate` without `--wait` (.github/workflows/docker-build-push.yml:109). A web container stuck in wait-for-db still gives a green deploy. **This is the real ops gap.**

## Why the proposal as written is wrong in one place
The proposed web healthcheck ("urllib to localhost:8000") fails in prod:
- With `DEBUG=False`, `SECURE_SSL_REDIRECT=True` (settings.py:99) returns a 301 to https://localhost:8000. urllib follows it and fails.
- `Host: localhost` returns a 400 unless prod `ALLOWED_HOSTS` (settings.py:43) contains localhost.
web would never become healthy. Any service with `depends_on: web: condition: service_healthy` (worker, caddy) would then never start, and `up --wait` would fail every deploy.

## Severity rationale
This is a single-host portfolio. The failure is visible in the logs, it is documented in the README, and only a misconfigured `.env` triggers it. Nothing is exploitable and no data can be lost, so it rates low.

## Better proposal (smallest diff)
1. On `db` only (both compose files), add a healthcheck: `test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]`, `interval: 5s`, `retries: 12`.
2. In web, worker and beat, change the `db` entry to `db: {condition: service_healthy}`. Keep redis as is: Celery retries the broker.
3. Delete `entrypoint:` (prod.yml:42, dev.yml:31), django/entrypoints/wait-for-db.sh, Dockerfile:29-30, and `postgresql-client` (Dockerfile:17). No other psql usage exists in the image; the backup docs run psql inside the db container.
   Result: a wrong password now makes `migrate` fail fast, and web exits (no restart policy, prod.yml:33) instead of looping silently.
4. Add `--wait` to docker-build-push.yml:109 so the deploy job fails when db is unhealthy or web exits.
5. Worker sleep: optional. It is now redundant for the DB. Dropping it plus `.env.example:47` is fine. The worst case is that one beat-overdue task runs before a fresh migration finishes and is retried on the next schedule.
6. Skip the web HTTP healthcheck. If one is wanted later, use a TCP check (`python -c "import socket;socket.create_connection(('127.0.0.1',8000),2)"`), not HTTP.

Effort: S. Test with `make dev-up` and with a deliberately wrong `DOCKER_DB_PASSWORD`.
