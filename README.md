# Django Portfolio Blog

The goal of the project was to create a portfolio using Django, PostgreSQL, and Tailwind. During implementation, DaisyUI was added as a plugin to Tailwind. The project was containerized to Docker Compose, has tests, and runs on DigitalOcean Droplet. The project is educational in nature.

## Running with Docker

### Prerequisites
- Docker
- Docker Compose

### Quick Start
```bash
# Rename .env.example to .env
# Change variables and secret key
cp .env.example .env

# Start all services in detached mode
docker-compose up --build -d

# To stop
docker-compose down
```

This will:
- Start PostgreSQL
- Start Redis
- Build and run Django with Gunicorn
- Start Celery worker
- Start Celery beat scheduler
- Serve static files through Caddy

Open `https://localhost`.

For rootless Podman, privileged host ports (`80`/`443`) are not available by default.
It's recommended to change ports then.
Open `https://localhost:{port}`.

## Local Setup

### Prerequisites
- Python 3.13+
- PostgreSQL
- Redis
- [uv](https://github.com/astral-sh/uv)
- Node.js + npm

### 1. Configure .env

```bash
# Rename .env.example to .env
# Change variables and secret key
cp .env.example .env
```

### 2. Create database
```sql
psql -U postgres
CREATE DATABASE your_db_name;
\q
```

### 3. Install and run
```bash
uv sync

# Generate Tailwind CSS
npm install
npm run build:css

# Run Django
python django/manage.py migrate
python django/manage.py collectstatic --noinput
python django/manage.py runserver

# Run Celery worker (second terminal)
celery -A personal_portfolio worker --workdir=django --loglevel=info

# Run Celery beat scheduler (third terminal)
celery -A personal_portfolio beat --workdir=django --loglevel=info

# Manual markdown sync from GitHub README links
python django/manage.py sync_project_markdowns
python django/manage.py sync_project_markdowns --slug my-django-portfolio
```
Open `http://localhost:8000`.

## Project Structure
```text
MY-DJANGO-PORTFOLIO/
|-- .github/
|-- django/
|   |-- entrypoints/
|   |-- main/
|   |-- personal_portfolio/
|   `-- manage.py
|-- media/
|-- staticfiles/
|-- Caddyfile
|-- docker-compose.yml
|-- Dockerfile
|-- LICENSE
|-- Makefile
|-- package-lock.json
|-- package.json
|-- pyproject.toml
|-- README.md
|-- tailwind.config.js
`-- uv.lock
```

## Technologies

- Python 3.13 + Django 5.1.7
- PostgreSQL
- Tailwind CSS + DaisyUI
- Docker + Docker Compose

## Features

- Project detail pages
- Blog pages routed by slug (`/blog/<slug>/`)
- Status and tag system
- Project filtering
- PostgreSQL-backed data model
- Visitor counter
- Responsive UI
- Media file handling
- Background task support with Celery + Redis
- Hourly markdown synchronization with Celery Beat (`main.tasks.sync_project_markdowns_task`)

## Environment Variables

Core environment variables are defined in `.env.example`.

Profile identity/contact data is stored in the database table `main_portfolioprofile` (editable via Django Admin).
The app uses the active profile record (`is_active=True`), and model defaults are used when creating the first profile row.

## Solved Problems

- Problem: startup `.sh` script failed because of CRLF line endings.
  Solution: convert script line endings to LF.

- Problem: Caddy failed with `server block without any key...`.
  Solution: set `APP_DOMAIN` in `.env` (for example `APP_DOMAIN=localhost`).

- Problem: Caddy failed with `open /etc/caddy/Caddyfile: permission denied` on Fedora/SELinux.
  Solution: use SELinux relabel option on bind mount: `./Caddyfile:/etc/caddy/Caddyfile:ro,Z` (already configured in `docker-compose.yml`).

- Problem: `permission denied while trying to connect to the Docker daemon socket`.
  Solution: run Docker commands with `sudo` or add your user to the `docker` group (`sudo usermod -aG docker $USER`) and re-login.

- Problem: missing static files after deploy.
  Solution: run `docker-compose exec web python manage.py collectstatic`.

- Problem: `style.css` stopped updating after project reorganization.
  Solution: run `npm run build:css` and use path `./django/main/static/src/css/input.css -> ./django/main/static/css/style.css`.

## Additional Developer Information

### Static Files
- Run `python django/manage.py collectstatic` for production static files.

### Frontend
1. Tailwind config is in `tailwind.config.js`.
2. Place static files in `django/main/static/`.

### Deployment
1. Gunicorn is used as the WSGI server.

## Author

- Name: Krystian Stasica
- Portfolio: krystianstasica.pl
- Email: krystian.stasica@outlook.com

## License

This project is available under the MIT License. See [LICENSE](LICENSE).
