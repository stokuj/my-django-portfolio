# Implementation Details

## Frontend Implementation

### Styling Pipeline

- Source CSS: `django/main/static/src/css/input.css`.
- Build output: `django/main/static/css/style.css`.
- Scripts in `package.json`:
  - `npm run build:css`
  - `npm run build:css:prod`
  - `npm run dev`

### Template Composition

- Base layout: `base.html`.
- Pages: `home/`, `about/`, and `projects/`
- Each project in projects has separawe link with slug_url:
- Page templates: home, projects, project detail, about, error templates, blog templates.
- Reusable fragments in `components/`.

For a structural view, see [`frontend.md`](frontend.md).

## Backend Implementation
TODO

## Runtime and Deployment

### Docker Compose Services

Defined in `docker-compose.yml`:

- `db`: PostgreSQL 13 with persistent volume.
- `redis`: Redis 7 for Celery broker/backend.
- `web`: Django app startup (`migrate`, `collectstatic`, Gunicorn).
- `worker`: Celery worker process.
- `beat`: Celery beat scheduler with persisted schedule file.
- `caddy`: reverse proxy plus static/media file serving.

### Caddy Integration

- Caddy reads `Caddyfile` and routes traffic to Django.
- Static and media volumes are mounted into Caddy for direct file serving.

## Development and Verification Workflow

### Setup

```bash
cp .env.example .env
uv sync
npm install
npm run build:css
```

### Core checks

```bash
uv run python django/manage.py check
uv run python django/manage.py makemigrations --check --dry-run
uv run python django/manage.py test
```

### Targeted test examples

```bash
uv run python django/manage.py test main
uv run python django/manage.py test main.tests.test_views
uv run python django/manage.py test main.tests.test_views.ViewsTest.test_home_view
```
ent flow).
