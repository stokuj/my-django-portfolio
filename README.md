# My Django Portfolio

My personal portfolio blog built with **Django**. It uses **Postgres** to store data, **Tailwind** for frontend styling, **Docker** for containerized deployment, and has asynchronous tasks with **Celery** + Redis. It also has optional integration with my other project **FastAPI** to get my GitHub contribution data. It uses GitHub Actions for **CI/CD** and is deployed on Digital Ocean droplet.

## Project Structure

```text
my_django_portfolio/
|- django/
|  |- config/                 # Project config
|  |- entrypoints/            # Container startup scripts
|  |- main/                   # Core app
|  |  |- models.py            
|  |  |- views.py             # Page/API views
|  |  |- tasks.py             # Celery tasks
|  |  |- templates/           # Django templates
|  |  |- static/              # CSS/JS/images
|  |  `- tests/               
|  `- manage.py               
|- docs/                      # Technical documentation
|- Caddyfile
|- docker-compose.yml
|- Dockerfile
|- package.json
|- pyproject.toml
`- README.md
```

## Features

- Portfolio project listing and detail pages
- Blog routing by slug (`/blog/<slug>/`)
- Tag and status-based project organization
- Responsive UI built with Tailwind CSS + DaisyUI
- Visitor counter middleware and profile-driven site metadata
- Background jobs with Celery worker + beat scheduler
- Scheduled markdown synchronization (`main.tasks.sync_project_markdowns_task`)
- Optional FastAPI heatmap integration (`/heatmap/me`) with cached snapshot storage

## Tech Stack

- Python 3.13, Django 5.1
- PostgreSQL, Redis
- Celery
- Tailwind CSS v4 with DaisyUI
- Gunicorn, Caddy
- Docker Compose

## Quick Start (Docker)

### Run

```bash
#check variables, use good secrets
cp .env.example .env 
docker compose up --build -d
```

Open `https://localhost`.

Stop services:

```bash
docker compose down
```

## Local Development

### Prerequisites

- Python 3.13+
- PostgreSQL
- Node.js + npm

### Setup

```bash
cp .env.example .env
uv sync
npm install
npm run build:css
```

### Run app and workers

```bash
uv run python django/manage.py migrate
uv run python django/manage.py collectstatic --noinput
uv run python django/manage.py runserver
```

In separate terminals:

```bash
uv run celery -A config worker --workdir=django --loglevel=info
uv run celery -A config beat --workdir=django --loglevel=info
```

Open `http://localhost:8000`.

## Verification Commands

## Documentation

- Architecture details: [`docs/architecture.md`](docs/architecture.md)
- Implementation details: [`docs/implementation.md`](docs/implementation.md)
- Frontend diagram: [`docs/frontend.md`](docs/frontend.md)

## Troubleshooting

- Caddy error `server block without any key`: set `APP_DOMAIN` in `.env` (for example, `APP_DOMAIN=localhost`).
- Docker socket permission error: add your user to the Docker group or run with elevated privileges.
- CSS not updating: run `npm run build:css` and verify input/output paths in `package.json`.
- SELinux bind mount issue with Caddyfile: use `:Z` relabel option (already configured in `docker-compose.yml`).
- `502 Bad Gateway` after changing DB name: if you change `DOCKER_DB_NAME`, create that database in PostgreSQL first, otherwise `web` can stay in `wait-for-db`.
- Markdown sync looks successful but files are not visible in app: ensure `worker` mounts `media_volume:/app/media`.
- Permission errors on static/media/celerybeat files in Docker: app containers run as non-root (`10001:10001`), so existing volumes may need a one-time ownership fix (`chown`).
- `UnicodeDecodeError` in templates/content: save text files as UTF-8.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
