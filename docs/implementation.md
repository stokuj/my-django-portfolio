# Implementation Details

## Repository Layout

- `django/config/`: Django project configuration (settings, URLs, WSGI/ASGI, Celery bootstrap).
- `django/main/`: application code (models, views, tasks, templates, static assets).
- `docs/`: architecture and implementation documentation.
- `infra/`: infrastructure files (`docker-compose.dev.yml`, `docker-compose.prod.yml`, `Dockerfile`, `Caddyfile`, `scripts/`).
- Root operational files: `Makefile`, `pyproject.toml`, `package.json`.

## Backend Implementation

### Configuration

Main configuration is in `django/config/settings.py`.

- Environment loading: `.env` values are parsed via `django-environ`.
- Database: configured through `DB_*` variables.
- Security: when `DJANGO_DEBUG` is false, secure cookies, SSL redirect, and HSTS are enabled.
- Static and media paths are configured for shared Docker volumes.

### Application Layer (`django/main`)

#### Middleware and Shared Context

- Visitor tracking middleware: `django/main/middleware.py`.
- Shared template context: `django/main/context_processors.py`.

### Asynchronous Jobs (Celery)

Celery tasks are implemented in `django/main/tasks.py`.

Key jobs:

- `refresh_portfolio_heatmap_cache_task`: refreshes and caches heatmap data (beat: every hour).
- `sync_project_markdowns_task`: synchronizes markdown from repository links (beat: every 2 hours).
- `check_disk_usage_task`: records free disk space for the admin About page (beat: daily at 06:00).

Common implementation patterns:

- Explicit error handling with safe user-facing messages.
- Status persistence with `update_fields` for partial model updates.
- Historical execution logging to `TaskExecutionLog`.

### Direct GitHub Heatmap Integration

Heatmap integration is implemented through `django/main/heatmap.py`, `django/main/github_client.py`, and related views/tasks.

- Configuration: Django reads `GITHUB_HEATMAP_TOKEN` from `.env`.
- Authorization: the same configured GitHub bearer token is used for all heatmap fetches.
- Fetch path: `fetch_heatmap_data()` sends one GitHub GraphQL `viewer` query that returns the token owner's login and contribution days.
- Caching path: valid payloads are normalized and saved to `HeatmapSnapshot`.
- Failure behavior: on token/network/upstream errors, Django stores an error message and can reuse the last valid snapshot.
- Scope note: GitHub login and social auth are not part of the runtime anymore.

### Markdown Synchronization

- Core sync logic: `django/main/markdown_sync.py`.
- Trigger methods:
  - scheduled via Celery beat,
  - manual via the staff-only POST route behind the About page admin tools (`run_markdown_sync_task`).
- Returned summary is stable and includes `total`, `updated`, `failed`, and per-project details.

## Frontend Implementation

### Styling Pipeline

- Input CSS: `django/main/static/src/css/input.css`.
- Output CSS: `django/main/static/css/style.css`.
- NPM scripts:
  - `npm run build:css`
  - `npm run build:css:prod`
  - `npm run dev`

### Template Composition

- Shared layout: `base.html`.
- Main page templates: home, projects, project detail, about, and error pages.
- Reusable fragments: `components/` templates.

For the visual template map, see [`frontend.md`](frontend.md).

## Runtime and Deployment

### Docker Compose Services

Production services are defined in `infra/docker-compose.prod.yml`:

- `db`: PostgreSQL 18 (volume `postgres18_data` mounted at `/var/lib/postgresql`).
- `redis`: broker/result backend for Celery.
- `web`: Django + Gunicorn.
- `worker`: Celery worker.
- `beat`: Celery beat scheduler.
- `caddy`: reverse proxy and static/media file server.

### Caddy Integration

- Caddy proxies dynamic traffic to Django.
- Static and media files are served directly from shared volumes.

### Development Compose Services

Local development uses `infra/docker-compose.dev.yml` with `db`, `redis`, `web`, `worker`, and `beat`. It does not include Caddy; Django is exposed directly on port `8000` via `runserver`.

### Backups and restore

- DigitalOcean droplet backups cover the whole disk, including the Docker volumes (database and media).
- Every deploy dumps the database before `up` (which runs `migrate`): `pg_dump -Fc` inside the `db` container, written to `~/backups/pre-deploy-YYYY-MM-DD-HHMM.dump` on the server. The dumps contain the whole database, including admin password hashes, so `~/backups` is `700` and each dump is `600`; keep them that way when copying them off the droplet. Dumps older than 14 days are deleted. The first deploy has no dump because `db` is not running yet.
- Restore a dump on the server (stop the app services so nothing writes meanwhile):

```bash
cd ~/my_django_portfolio
C="docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml"
$C stop web worker beat
$C exec -T db sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < ~/backups/pre-deploy-YYYY-MM-DD-HHMM.dump
$C start web worker beat
```

- If the dump is a rollback from a bad release, start the previous image instead of the current one: `IMAGE_TAG=<previous sha> $C up -d --wait`.

### Disk monitoring

Disk alerting lives in DigitalOcean Monitoring (alert at 85% disk usage, by email). The daily `check_disk_usage_task` only records its result for the admin About page and notifies nobody.

## New droplet bootstrap

Owner steps, in order, for the new droplet. They need the server, the DigitalOcean console or GitHub secrets. Nothing is migrated from the archived droplet: PostgreSQL 18 starts on an empty `postgres18_data` volume, content is re-entered in admin, and heatmap and blog markdown refill from GitHub.

1. [ ] Create the droplet with DigitalOcean backups enabled.
2. [ ] Add a DigitalOcean Monitoring alert: disk usage above 85%, notify by email.
3. [ ] Install Docker Engine with the Compose plugin and let `SERVER_USER` run `docker`.
4. [ ] Clone the repository to `~/my_django_portfolio` (the deploy job runs from there).
5. [ ] Write the server `.env` from `.env.example`: `DJANGO_DEBUG=False`, a long random `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `APP_DOMAIN`/`APP_WWW_DOMAIN`, new `DOCKER_DB_*` credentials, `GITHUB_HEATMAP_TOKEN` and the `PORTFOLIO_*` values.
6. [ ] Set `ADMIN_BASIC_USER` and `ADMIN_BASIC_HASH` in the server `.env` (hash from `docker run --rm caddy:2 caddy hash-password`, single-quoted). Without them Caddy will not start.
7. [ ] Set the GitHub secrets `SERVER_HOST`, `SERVER_USER` and `SSH_PRIVATE_KEY`.
8. [ ] Add the `SERVER_SSH_FINGERPRINT` GitHub secret: the SHA256 value from `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub | awk '{print $2}'`, run on the droplet (not via `ssh-keyscan`). Update it if the droplet or its host key changes.
9. [ ] Run the first deploy: merge the `dev → main` PR. The `db` service initialises an empty PostgreSQL 18 database and `web` runs `migrate`.
10. [ ] Watch the first deploy: follow the Actions log until the job is green, then run `docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml ps` on the droplet and check that every service is up and `db` is healthy.
11. [ ] Create the admin account: `docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml exec web python manage.py createsuperuser`.
12. [ ] Re-enter projects, tags, the portfolio profile and thumbnails in admin.
13. [ ] Log in and trigger both sync jobs on `/about` ("Sync Heatmap" and "Sync Markdown").
14. [ ] After the first successful deploy (GHCR login uses the job's `GITHUB_TOKEN`), delete the `GHCR_PAT` and `GHCR_USERNAME` GitHub secrets.

## Development and Verification Workflow

### Setup

```bash
uv sync --extra dev
npm install
make dev-up
```

`make dev-up` creates `.env` from `.env.example` automatically when the file does not exist.

### Core Checks

```bash
make verify
```

### Targeted Test Examples

```bash
uv run python django/manage.py test main
uv run python django/manage.py test main.tests.test_views
uv run python django/manage.py test main.tests.test_views.ViewsTest.test_home_view
```

## Documentation Maintenance Guidelines

- Keep commands aligned with actual scripts and runtime behavior.
- Update architecture docs when adding services, queues, or external integrations.
- Update this file whenever module structure, background jobs, or deployment flow changes.
