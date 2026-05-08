# Implementation Details

## Repository Layout

- `django/config/`: Django project configuration (settings, URLs, WSGI/ASGI, Celery bootstrap).
- `django/main/`: application code (models, views, tasks, templates, static assets).
- `django/entrypoints/`: container startup scripts.
- `docs/`: architecture and implementation documentation.
- Root operational files: `docker-compose.yml`, `Dockerfile`, `Caddyfile`, `pyproject.toml`, `package.json`.

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

- `healthcheck_task`: worker health check.
- `sync_project_markdowns_task`: synchronizes markdown from repository links.
- `refresh_portfolio_heatmap_cache_task`: refreshes and caches heatmap data.

Common implementation patterns:

- Explicit error handling with safe user-facing messages.
- Status persistence with `update_fields` for partial model updates.
- Historical execution logging to `TaskExecutionLog`.

### Direct GitHub Heatmap Integration

Heatmap integration is implemented through `django/main/heatmap.py`, `django/main/github_client.py`, and related views/tasks.

- Configuration: Django reads `GITHUB_HEATMAP_TOKEN` from `.env`.
- Authorization: the same configured GitHub bearer token is used for all heatmap fetches.
- Fetch path: `fetch_heatmap_data(github_token=None)` resolves the token owner through GitHub REST and then fetches contribution days through GitHub GraphQL.
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

Services are defined in `docker-compose.yml`:

- `db`: PostgreSQL.
- `redis`: broker/result backend for Celery.
- `web`: Django + Gunicorn.
- `worker`: Celery worker.
- `beat`: Celery beat scheduler.
- `caddy`: reverse proxy and static/media file server.

### Caddy Integration

- Caddy proxies dynamic traffic to Django.
- Static and media files are served directly from shared volumes.

## Development and Verification Workflow

### Setup

```bash
cp .env.example .env
uv sync
npm install
npm run build:css
```

### Core Checks

```bash
SECRET_KEY=test DJANGO_DEBUG=True uv run python django/manage.py check
SECRET_KEY=test DJANGO_DEBUG=True uv run python django/manage.py makemigrations --check --dry-run
SECRET_KEY=test DJANGO_DEBUG=True uv run python django/manage.py test main -v 2
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
