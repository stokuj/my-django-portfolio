# sec-infra

Scope: infra/Caddyfile, infra/Dockerfile, infra/docker-compose.{dev,prod}.yml, django/entrypoints/wait-for-db.sh (HEAD of `dev`).

## 1. web and caddy have no restart policy in prod
- Severity: high | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:33, infra/docker-compose.prod.yml:153
- Problem: db, redis, worker, beat use `restart: always`; `web` (33-74) and `caddy` (153-178) have none. After a droplet reboot, Docker daemon restart or a gunicorn crash, these two stay stopped and the site is down while the workers keep running.
- Proposal: add `restart: always` to `web` and `caddy`.
- Risk: none.

## 2. PostgreSQL 13 is EOL (no security patches since Nov 2025)
- Severity: high | Category: security | Effort: M
- File: infra/docker-compose.prod.yml:3, infra/docker-compose.dev.yml:3
- Problem: `image: postgres:13`. Upgrade to 16 was reverted in b8da60e ("migration deferred"); prod has run an unsupported DB for ~11 months.
- Proposal: pg_dump from 13, start `postgres:16` (or 17) on a fresh volume, restore; same tag in dev.
- Risk: data migration; take a dump and keep the old volume until verified.

## 3. Caddy serves static/media without security headers
- Severity: medium | Category: security | Effort: S
- File: infra/Caddyfile:18-26
- Problem: `/static/*` and `/media/*` bypass Django, so `SecurityMiddleware` headers (nosniff, Referrer-Policy) are absent. `/media/` holds admin-uploaded files (`thumbnails/`, `blog_markdown/`, django/main/models.py:59-61) served inline from the main origin with no `X-Content-Type-Options: nosniff` and no sandboxing.
- Proposal: in the `https://{$APP_DOMAIN}` block add `header { X-Content-Type-Options nosniff; Referrer-Policy same-origin; -Server }` and for `/media/*` additionally `Content-Security-Policy "default-src 'none'; img-src 'self'; sandbox"`.
- Risk: low; check thumbnails still render.

## 4. No Content-Security-Policy; third-party script floating and without SRI
- Severity: medium | Category: security | Effort: M
- File: django/main/templates/projects/detail.html:52, django/config/settings.py:57-66, infra/Caddyfile:16
- Problem: no CSP is set anywhere (no middleware, no Caddy header). project detail loads `https://cdn.jsdelivr.net/npm/mathjax@3/...` (floating major, no `integrity`), so a CDN/package compromise runs JS on the site with the admin session cookie origin. Inline scripts exist in about.html:258, 468.
- Proposal: pin exact MathJax version + `integrity`/`crossorigin` (or self-host in static). Add CSP (Caddy header or django-csp), start with `Content-Security-Policy-Report-Only`; move about.html inline scripts to static files.
- Risk: CSP can break MathJax / inline scripts; roll out report-only first.

## 5. Docker image ignores uv.lock; uv itself unpinned
- Severity: medium | Category: security | Effort: S
- File: infra/Dockerfile:21, infra/Dockerfile:26-27, pyproject.toml:29-30
- Problem: `uv.lock` is copied but `uv pip install --system .` resolves from pyproject, and `[tool.uv] pip = { upgrade = true }` forces fresh resolution of all transitive deps on every build. Prod deps are not reproducible and lockfile/Dependabot fixes do not govern them. `pip install uv` is unpinned.
- Proposal: `COPY --from=ghcr.io/astral-sh/uv:<x.y.z> /uv /bin/uv` and install from the lock (`uv export --frozen --no-dev -o req.txt && uv pip install --system -r req.txt .` or `uv sync --frozen --no-dev`).
- Risk: low; versions become those in uv.lock.

## 6. Runtime user owns the application code
- Severity: medium | Category: security | Effort: S
- File: infra/Dockerfile:33-36, infra/docker-compose.prod.yml:33-151
- Problem: `chown -R app:app /app` makes all source (`/app/django/**/*.py`) writable by uid 10001, so an RCE in Django/Celery can persist by modifying code. No `read_only`, `cap_drop`, or `no-new-privileges` in compose.
- Proposal: chown only `/app/staticfiles /app/media /app/django/celerybeat-schedule`; optionally add `security_opt: [no-new-privileges:true]` and `cap_drop: [ALL]` to web/worker/beat.
- Risk: low; verify collectstatic and beat schedule writes still work.

## 7. Floating base image tags, app deployed as :latest
- Severity: low | Category: security | Effort: S
- File: infra/Dockerfile:2, infra/Dockerfile:10, infra/docker-compose.prod.yml:3,23,37,154
- Problem: `node:22-slim`, `python:3.13-slim`, `caddy:2`, `redis:7-alpine`, `postgres:13`, app `:latest` - no digests; builds are not reproducible and deploy has no rollback tag. No `.github/dependabot.yml` docker ecosystem to bump pins.
- Proposal: tag app image with commit SHA in addition to latest; pin base images to minor (+digest) and add Dependabot `docker` ecosystem.
- Risk: none.

## 8. Build toolchain shipped in runtime image
- Severity: low | Category: security | Effort: S
- File: infra/Dockerfile:16-18
- Problem: `gcc` and `libpq-dev` are installed in the final image although `psycopg2-binary` (pyproject.toml:16) needs neither. Extra attack surface and size.
- Proposal: drop `gcc libpq-dev` (keep `postgresql-client` only while wait-for-db.sh needs psql).
- Risk: build fails only if a dep without wheels appears; CI catches it.

## 9. No healthchecks; startup ordering by sleep
- Severity: low | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:65-67, 86-88, 142-144
- Problem: no `healthcheck` on any service; `depends_on` has no conditions; worker waits fixed `sleep 45`; beat starts with no DB wait at all.
- Proposal: healthcheck on db (`pg_isready`) and redis (`redis-cli ping`), `depends_on: {db: {condition: service_healthy}}`; then drop the sleep and wait-for-db.sh.
- Risk: low.

## 10. Prod DB published to host loopback
- Severity: low | Category: security | Effort: S
- File: infra/docker-compose.prod.yml:10-11
- Problem: `127.0.0.1:15432:5432` in prod; not internet-exposed, but any local process/user on the droplet can reach Postgres. Not needed by the app.
- Proposal: remove `ports` from prod db (use `docker compose exec db psql` or SSH tunnel to the container when needed).
- Risk: none for the app.

## 11. Flat network: caddy can reach db and redis; redis has no auth
- Severity: low | Category: security | Effort: S
- File: infra/docker-compose.prod.yml:22-31, 172-173, 180-182
- Problem: single `app-network`; the internet-facing caddy container can reach Postgres and unauthenticated Redis (Celery broker -> task injection if caddy is compromised).
- Proposal: put caddy and web on a `frontend` network, db/redis/web/worker/beat on `backend`.
- Risk: low.

## 12. Whole .env injected into every app container, env duplicated 3x
- Severity: low | Category: simplification | Effort: S
- File: infra/docker-compose.prod.yml:39-64, 83-103, 123-141
- Problem: `env_file: ../.env` already passes SECRET_KEY etc.; the `environment` blocks repeat them in three services. Every container (incl. beat) also gets GITHUB_HEATMAP_TOKEN and host-only DB_* creds.
- Proposal: one `x-app-env: &app-env` anchor with only the needed vars (DB_* mapping, CELERY_*), drop the duplicates.
- Risk: none if the variable set stays equal.

## 13. wait-for-db.sh loops forever
- Severity: low | Category: ops | Effort: S
- File: django/entrypoints/wait-for-db.sh:15-18
- Problem: no timeout; a wrong password/DB name hangs `web` forever printing "unavailable" instead of failing.
- Proposal: superseded by finding 9; otherwise use `pg_isready` with a max attempt count and `exit 1`.
- Risk: none.
