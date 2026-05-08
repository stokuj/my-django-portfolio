# My Django Portfolio

My personal portfolio blog built with **Django**. It uses **Postgres** to store data, **Tailwind** for frontend styling, **Docker** for containerized deployment, and has asynchronous tasks with **Celery** + Redis. It fetches GitHub contribution data directly from the GitHub API and uses GitHub Actions for **CI/CD**.

The key feature is that the app pulls Markdown from GitHub **README.MD** files and shows it on blog pages, and Celery keeps this content updated in the background.

---
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
|- docker-compose.dev.yml
|- docker-compose.prod.yml
|- Dockerfile
|- Makefile
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
- GitHub contribution heatmap data endpoint (`/about/heatmap-data/`) with cached snapshot storage

## Tech Stack

- Python 3.13, Django 5.1
- PostgreSQL, Redis
- Celery
- Tailwind CSS v4 with DaisyUI
- Gunicorn, Caddy
- Docker Compose

## Showcase

### Home page
A hero banner with floating tech keywords in the background. Below it, a project timeline split into Planned, Ongoing, and Finished sections — each collapsible.
<img width="2267" height="1645" alt="image" src="https://github.com/user-attachments/assets/6d4fbcaf-b200-47de-9982-abc8e5d10fc1" />

### Projects page
A filterable grid of projects. You can search by name or filter by technology tags like Django, Python, Docker, etc. Each card shows a project thumbnail, description, status badge, and a "View Project" button.
<img width="2267" height="1334" alt="screencapture-localhost-projects-2026-02-22-15_13_50" src="https://github.com/user-attachments/assets/25a3085e-edf2-45aa-93b9-42c47f36e2f9" />

### About page
The main landing page showing a brief intro ("Hi, I am John Doe"), tech stack badges, current learning goals, and a live GitHub contributions heatmap fetched directly by Django from GitHub.
<img width="2267" height="1669" alt="image" src="https://github.com/user-attachments/assets/5e01c6d9-9e82-4745-8210-7076888c9722" />

### Dark theme
All backgrounds, text, and cards switch to dark colors. The accent color shifts to green.
<img width="2267" height="1486" alt="image" src="https://github.com/user-attachments/assets/21b6ea0b-0625-4202-9176-3b4e24ed108b" />

### About when logged as admin (page owner)
The about page with extra admin controls visible, including a Scheduled Jobs panel showing Celery tasks (heatmap refresh, markdown sync) and an Executed Tasks panel with task history and run timestamps.
<img width="2267" height="2843" alt="image" src="https://github.com/user-attachments/assets/17c53ec4-56ae-4acb-8e3b-da50f7059f4c" />

## Quick Start (Docker)

### Development

```bash
make dev-up
make dev-status
make dev-down
```

Open `http://localhost:8000`.

`make dev-up` creates `.env` from `.env.example` when needed.

### Production

```bash
make prod-up
make prod-status
make prod-down
```

`make prod-up` requires an existing `.env` file and fails if it is missing.

## Local Development

### Prerequisites

- Python 3.13+
- PostgreSQL
- Redis (required for Celery worker/beat)
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
make verify
```

## Heatmap Configuration

- Set `GITHUB_HEATMAP_TOKEN` in `.env` to enable the portfolio heatmap.
- Django fetches the configured token owner and contribution calendar directly from GitHub and caches the normalized payload in `HeatmapSnapshot`.
- GitHub login/auth integration is not part of this project.

## Documentation

- Architecture details: [`docs/architecture.md`](docs/architecture.md)
- Implementation details: [`docs/implementation.md`](docs/implementation.md)
- Frontend diagram: [`docs/frontend.md`](docs/frontend.md)

## Troubleshooting

- Caddy TLS for `www` fails (`ERR_SSL_PROTOCOL_ERROR`): set both `APP_DOMAIN` and `APP_WWW_DOMAIN` in `.env` (for example, `APP_DOMAIN=krystianstasica.pl`, `APP_WWW_DOMAIN=www.krystianstasica.pl`).
- Docker socket permission error: add your user to the Docker group or run with elevated privileges.
- CSS not updating: run `npm run build:css` and verify input/output paths in `package.json`.
- SELinux bind mount issue with Caddyfile: use `:Z` relabel option (already configured in `docker-compose.prod.yml`).
- `502 Bad Gateway` after changing DB name: if you change `DOCKER_DB_NAME`, create that database in PostgreSQL first, otherwise `web` can stay in `wait-for-db`.
- Markdown sync looks successful but files are not visible in app: ensure `worker` mounts `media_volume:/app/media`.
- Permission errors on static/media/celerybeat files in Docker: app containers run as non-root (`10001:10001`), so existing volumes may need a one-time ownership fix (`chown`).
- `UnicodeDecodeError` in templates/content: save text files as UTF-8.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
