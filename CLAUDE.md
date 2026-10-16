# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Full verification (what CI runs)
```bash
make verify
```
Runs the CSS build, compileall, `manage.py check`, `makemigrations --check`, `manage.py test main tests` on SQLite (app and operational tests), and `ruff check .` over the whole repo.

### Development with Docker
```bash
make dev-up      # builds and starts all services; creates .env from .env.example if missing
make dev-status  # show running containers
make dev-down
```

### Running tests
```bash
# Django app tests (requires env vars for settings)
SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 DB_ENGINE=django.db.backends.sqlite3 uv run python django/manage.py test main

# Run a single test module
SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 DB_ENGINE=django.db.backends.sqlite3 uv run python django/manage.py test main.tests.test_views

# Operational tests (deploy workflow invariants; no env vars needed)
uv run python -m unittest discover -s tests -t .
```

### Linting
```bash
uv run ruff check .
```

### CSS build
```bash
npm run build:css        # development (watch with: npm run dev)
npm run build:css:prod   # minified for production
```

### Django management
```bash
uv run python django/manage.py migrate
uv run python django/manage.py collectstatic --noinput
uv run python django/manage.py runserver
```

### Celery (separate terminals)
```bash
uv run celery -A config worker --workdir=django --loglevel=info
uv run celery -A config beat --workdir=django --loglevel=info
```

## Architecture

### Service topology
Six Docker services in production: `web` (Gunicorn+Django), `db` (PostgreSQL), `redis`, `worker` (Celery worker), `beat` (Celery beat scheduler), `caddy` (reverse proxy + static/media serving). Dev compose omits Caddy. `db` has a `pg_isready` healthcheck; `web`, `worker` and `beat` wait for `service_healthy`. PostgreSQL 18 data lives in `postgres18_data` (dev: `postgres18_dev_data`) mounted at `/var/lib/postgresql`. Gunicorn runs `--workers 1 --threads 4 --timeout 60`.

### Django app layout
Single app `main` under `django/`. Configuration lives in `django/config/` (settings, urls, celery, wsgi/asgi). The `django/` directory is both the Django project root and the `--workdir` for Celery.

### Key modules
- `django/main/models.py` — all domain models: `Project`, `Tag`, `PortfolioProfile`, `HeatmapSnapshot`, `PageView`, `TaskExecutionLog`
- `django/main/views.py` — page views, the heatmap JSON endpoint (serves the stored snapshot and enqueues a refresh when stale) and admin-tool endpoints
- `django/main/tasks.py` — Celery tasks: `sync_project_markdowns_task`, `refresh_portfolio_heatmap_cache_task` and `check_disk_usage_task`
- `django/main/markdown_sync.py` — fetches the README of each project's `github_url` and writes it to `media/blog_markdown/`
- `django/main/heatmap.py` — fetches GitHub contribution data (one GraphQL query) and persists to `HeatmapSnapshot`
- `django/main/context_processors.py` — injects visitor count, project count, and the active profile (`PortfolioProfile.get_active()`) into every template

### Background task observability
Every task run appends a `TaskExecutionLog` row; the newest row per `task_name` is that task's current status. Rows older than 90 days are pruned. Admin users see this on the about page.

### Environment variables
Loaded from `.env` at project root via `django-environ`. `SECRET_KEY` is required at startup. Key vars: `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `GITHUB_HEATMAP_TOKEN`, `HEATMAP_CACHE_TTL_MINUTES`, `CELERY_BROKER_URL`, `DB_*` (or `DOCKER_DB_*` for compose), `ADMIN_BASIC_USER`/`ADMIN_BASIC_HASH` (Caddy). See `.env.example`.

### Static and media files
- CSS source: `django/main/static/src/css/input.css` → output: `django/main/static/css/style.css`
- Caddy serves `staticfiles/` and `media/` directly via named Docker volumes
- Caddy also puts `basic_auth` on `/admin*`, serves `robots.txt`, compresses responses (zstd/gzip) and caps request bodies at 10MB
- Containers run as non-root uid `10001:10001`; volume ownership matters

### Celery beat schedule
Defined in `django/config/settings.py` (`CELERY_BEAT_SCHEDULE`):
- Heatmap refresh: every hour
- Markdown sync: every 2 hours
- Disk usage check: daily at 06:00

### Tests location
- `django/main/tests/` — Django unit/integration tests (views, models, tasks, middleware, heatmap, markdown sync)
- `tests/` — operational tests for the deploy workflow script order (no Django required)

### CI/CD
Two GitHub Actions workflows: `django.yml` runs `make verify` and validates the prod compose file on push and PR to main; `docker-build-push.yml` runs on push to main, calls `django.yml` first, then builds and pushes the image to GHCR as `:<sha>` and `:latest`, and deploys to DigitalOcean via SSH (host fingerprint verified). The deploy checks out the sha, pulls `IMAGE_TAG=<sha>`, runs `check --deploy`, takes a `pg_dump` to `~/backups` (14-day retention), then `up -d --remove-orphans --wait`. Dependabot opens monthly grouped updates. Production is currently off; see "New droplet bootstrap" in `docs/implementation.md`.
