# My Django Portfolio

My personal portfolio blog built with Django. It uses Postgres to store data, Tailwind for frontend styling, Docker for xyz and has asynchronus Tasks with. It also has optional integration with my other project FastAPI to get my github contriubution.


## Features

- Portfolio project listing and detail pages
- Blog routing by slug (`/blog/<slug>/`)
- Tag and status-based project organization
- Responsive UI built with Tailwind CSS + DaisyUI
- Visitor counter middleware and profile-driven site metadata
- Background jobs with Celery worker + beat scheduler
- Scheduled markdown synchronization (`main.tasks.sync_project_markdowns_task`)

## Tech Stack

- Python 3.13, Django 5.1
- PostgreSQL, Redis
- Celery
- Tailwind CSS v4, DaisyUI
- Gunicorn, Caddy
- Docker Compose

## Quick Start (Docker)

### Prerequisites

- Docker
- Docker Compose

### Run

```bash
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
- Redis
- [uv](https://github.com/astral-sh/uv)
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

```bash
uv run python django/manage.py check
uv run python django/manage.py makemigrations --check --dry-run
uv run python django/manage.py test
```

## Project Structure

```text
my_django_portfolio/
|- django/
|  |- config/
|  |- entrypoints/
|  |- main/
|  `- manage.py
|- docs/
|- Caddyfile
|- docker-compose.yml
|- Dockerfile
|- package.json
|- pyproject.toml
`- README.md
```

## Documentation

- Documentation index: [`docs/README.md`](docs/README.md)
- Architecture details: [`docs/architecture.md`](docs/architecture.md)
- Implementation details: [`docs/implementation.md`](docs/implementation.md)
- Frontend diagram: [`docs/frontend.md`](docs/frontend.md)

## Troubleshooting

- Caddy error `server block without any key`: set `APP_DOMAIN` in `.env` (for example, `APP_DOMAIN=localhost`).
- Docker socket permission error: add your user to the Docker group or run with elevated privileges.
- CSS not updating: run `npm run build:css` and verify input/output paths in `package.json`.
- SELinux bind mount issue with Caddyfile: use `:Z` relabel option (already configured in `docker-compose.yml`).

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
