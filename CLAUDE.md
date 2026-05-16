# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Full verification (what CI runs)
```bash
make verify
```
Runs CSS build, Python compile check, `manage.py check`, migration check, Django tests, and ruff lint.

### Development with Docker
```bash
make dev-up      # builds and starts all services; creates .env from .env.example if missing
make dev-status  # show running containers
make dev-down
```

### Running tests
```bash
# Django app tests (requires env vars for settings)
SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test

# Run a single test module
SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test main.tests.test_views

# Operational/infra tests (no env vars needed)
uv run python -m pytest tests/
```

### Linting
```bash
uv run ruff check infra/scripts tests
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
Six Docker services in production: `web` (Gunicorn+Django), `db` (PostgreSQL), `redis`, `worker` (Celery worker), `beat` (Celery beat scheduler), `caddy` (reverse proxy + static/media serving). Dev compose omits Caddy.

### Django app layout
Single app `main` under `django/`. Configuration lives in `django/config/` (settings, urls, celery, wsgi/asgi). The `django/` directory is both the Django project root and the `--workdir` for Celery.

### Key modules
- `django/main/models.py` — all domain models: `Project`, `Tag`, `PortfolioProfile`, `HeatmapSnapshot`, `PageView`, `TaskExecutionStatus`, `TaskExecutionLog`
- `django/main/views.py` — page views and admin-tool endpoints
- `django/main/tasks.py` — two main Celery tasks: `sync_project_markdowns_task` and `refresh_portfolio_heatmap_cache_task`
- `django/main/markdown_sync.py` — fetches README markdown from GitHub and writes to `media/blog_markdown/`
- `django/main/heatmap.py` — fetches GitHub contribution data (REST + GraphQL) and persists to `HeatmapSnapshot`
- `django/main/context_processors.py` — injects visitor count, project count, and active `PortfolioProfile` into every template

### Background task observability
Every task run writes to `TaskExecutionStatus` (latest snapshot, keyed by `task_name`) and appends a `TaskExecutionLog` row. Admin users see this on the about page.

### Environment variables
Loaded from `.env` at project root via `django-environ`. `SECRET_KEY` is required at startup. Key vars: `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `GITHUB_HEATMAP_TOKEN`, `HEATMAP_CACHE_TTL_MINUTES`, `CELERY_BROKER_URL`, `DB_*` (or `DOCKER_DB_*` for compose). See `.env.example`.

### Static and media files
- CSS source: `django/main/static/src/css/input.css` → output: `django/main/static/css/style.css`
- Caddy serves `staticfiles/` and `media/` directly via named Docker volumes
- Containers run as non-root uid `10001:10001`; volume ownership matters

### Celery beat schedule
Defined in `django/config/settings.py` (`CELERY_BEAT_SCHEDULE`):
- Heatmap refresh: every hour
- Markdown sync: every 2 hours

### Tests location
- `django/main/tests/` — Django unit/integration tests (views, models, tasks, middleware, heatmap, markdown sync)
- `tests/` — operational tests for infra scripts and compose file invariants (no Django required)

### CI/CD
Two GitHub Actions workflows: `django-ci.yml` runs `make verify` on PRs to main; `docker-build-push.yml` builds and pushes to GHCR then deploys to DigitalOcean via SSH on merge to main.
