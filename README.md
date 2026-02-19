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
- Build and run Django with Gunicorn
- Serve static files through Caddy

Open `https://localhost`.

For rootless Podman, privileged host ports (`80`/`443`) are not available by default.
This project maps Caddy to non-privileged host ports out of the box (`8080` and `8443`),
so open `https://localhost:8443`.

## Local Setup

### Prerequisites
- Python 3.13+
- PostgreSQL
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

## Environment Variables

Core environment variables are defined in `.env.example`.

Important optional profile variables:
- `PORTFOLIO_SITE_NAME`
- `PORTFOLIO_FULL_NAME`
- `PORTFOLIO_ROLE_LINE`
- `PORTFOLIO_SPECIALIZATION_LINE`
- `PORTFOLIO_EMAIL`
- `PORTFOLIO_GITHUB_URL`
- `PORTFOLIO_LINKEDIN_URL`

These values are rendered in templates via a Django context processor, so you can update site identity and contact details without editing templates.

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
