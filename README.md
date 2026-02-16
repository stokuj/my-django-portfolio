# Django Portfolio Blog

This repository contains a Django portfolio/blog project using PostgreSQL.

## Running with Docker

### Prerequisites
- Docker
- Docker Compose

### Quick Start
```bash
# Rename .env.example to .env
cp .env.example .env

# Start all services in detached mode
docker-compose up --build -d
```

This will:
- Start PostgreSQL
- Build and run Django with Gunicorn
- Serve static files through Caddy
- Run `web` from the image filesystem (no source bind mount to `/app`)

Open `https://localhost`.

To stop:
```bash
docker-compose down
```

## Local Setup

### Prerequisites
- Python 3.x
- PostgreSQL
- [uv](https://github.com/astral-sh/uv)

### 1. Clone
```bash
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### 2. Configure env
```bash
cp .env.example .env
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Create database
```sql
psql -U postgres
CREATE DATABASE your_db_name;
\q
```

### 4. Install and run
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

- Python 3.13
- Django 5.1.7
- PostgreSQL
- Tailwind CSS + DaisyUI
- Gunicorn
- Docker + Docker Compose

## Features

- Project detail pages
- Status and tag system
- Project filtering
- PostgreSQL-backed data model
- Visitor counter
- Responsive UI
- Media file handling

## Solved Problems

- Problem: startup `.sh` script failed because of CRLF line endings.
  Solution: convert script line endings to LF.

- Problem: Caddy failed with `server block without any key...`.
  Solution: set `APP_DOMAIN` in `.env` (for example `APP_DOMAIN=localhost`).

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
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## License

This project is available under the MIT License. See [LICENSE](LICENSE).
