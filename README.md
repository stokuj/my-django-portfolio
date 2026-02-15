# 📝 Django Portfolio Blog

This repository contains a simple blog created with Django using PostgreSQL as the database. The application is part of my portfolio and aims to showcase my skills in backend development, database work, and the Django framework.

## 🐳 Running with Docker

### Prerequisites
- Docker
- Docker Compose

### Quick Start
```bash
# Rename .env.example to .env
cp .env.example .env

# Start all services
# (-d) (detached mode) containter will work in background
docker-compose up --build -d
```

This will:
- Start PostgreSQL container
- Build and run Django with Gunicorn
- Serve static files via Caddy reverse proxy

Access the app at `http://localhost`

To stop:
```bash
docker-compose down
```


## 🚀 Local Setup

### Prerequisites
- Python 3.x
- PostgreSQL installed and running
- [uv](https://github.com/astral-sh/uv) package manager

### Step 1: Clone the repository
```bash
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### Step 2: Configure environment variables

Rename `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```

**Generate a secure SECRET_KEY:**
```bash
# Using Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key and paste it into your `.env` file:
```bash
SECRET_KEY=your_generated_secure_key_here
```

### Step 3: Create PostgreSQL database

Create a database matching the `DB_NAME` in your `.env` file:
```sql
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE your_db_name;

# Exit
\q
```

### Step 4: Install dependencies and run
```bash
# Install dependencies with uv
uv sync

# Apply migrations and start server
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Access the app at `http://localhost`

---
## ⚠️ Common Issues

### 1. Line Ending Issues (CRLF vs LF)

**Problem:** Script fails with errors like `set: Illegal option -` or `: not found`

**Solution:** Or configure your editor to use LF line endings for `.sh` files.

---

### 2. Caddyfile Configuration Error

**Problem:** `Error: server block without any key is global configuration, and if used, it must be first`

**Cause:** Missing `APP_DOMAIN` variable in `.env` file, causing Caddy to see an empty block.

**Solution:** Add to your `.env`:
```bash
APP_DOMAIN=localhost  # For development
# APP_DOMAIN=yourdomain.com  # For production
```

For local development, comment out the production block in `Caddyfile`:
```caddy
# Production - uncomment when deploying
# {$APP_DOMAIN} {
#     ...
# }
```

---

### 3. Digital Ocean Deployment Issues

**Common issues when deploying to Digital Ocean:**

**Problem:** `Missing Static Files`

**Solution:** Run `docker-compose exec web python manage.py collectstatic` if files are missing

## 📁 Project Structure
    MY-DJANGO-PORTFOLIO/
    │
    ├── main/                      # Main application containing models, views, and templates
    │   ├── migrations/            # Database migrations
    │   ├── static/                # Static files (CSS, images)
    │   ├── templates/             # HTML templates
    │   │   └── main/
    │   │       ├── blog/          # Each project has its own subpage
    │   │       ├── about.html     # About page
    │   │       ├── home.html      # Home page
    │   │       └── projects.html  # Projects list
    │   │   └── base.html          # Base template
    │   ├── __init__.py
    │   ├── admin.py               # Admin panel configuration
    │   ├── apps.py                # Application configuration
    │   ├── context_processors.py  # Context processors
    │   ├── models.py              # Data models
    │   ├── tests.py               # Tests
    │   ├── urls.py                # URL configuration
    │   └── views.py               # Views
    ├── media/                     # User-uploaded files
    ├── node_modules/              # Node.js dependencies
    ├── personal_portfolio/        # Main project directory
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── asgi.py                # ASGI configuration
    │   ├── settings.py            # Project settings
    │   ├── urls.py                # Main project URLs
    │   └── wsgi.py                # WSGI configuration
    ├── staticfiles/               # Collected static files for production
    ├── LICENSE                    # Project license
    ├── manage.py                  # Django management script
    ├── package-lock.json          # npm dependencies (lock)
    ├── package.json               # npm configuration
    ├── Procfile                   # Heroku configuration
    ├── README.md                  # Project documentation
    ├── requirements.txt           # Python dependencies
    └── tailwind.config.js         # Tailwind CSS configuration

## 🔧 Technologies

- Python 3.13
- Django 5.1.7
- PostgreSQL
- Django Templates (HTML + Tailwind)
- DaisyUI plugin for Tailwind
- Gunicorn as WSGI server
- Docker and Docker Compose
- WhiteNoise for static files handling
- CKEditor, TinyMCE, and Summernote as rich text editors

## ⚙️ Features

- Each project has its own subpage
- Status and tag system for projects
- Dynamic project filtering
- PostgreSQL stores projects as objects
- Page visit counter
- Responsive user interface with Tailwind CSS
- Multimedia file handling
- Rich Text editors
- Database query optimization

## 🔍 Additional Developer Information

### Rich Text Editors

### Static Files Handling

- WhiteNoise is configured to compress static files in production
- Run `python manage.py collectstatic` to collect static files for production

### Frontend

1. The project uses Tailwind CSS with the DaisyUI plugin for styling
2. Tailwind configuration is in the `tailwind.config.js` file
3. Place static files in the `main/static/` directory

### Deployment Notes

1. Gunicorn is used as the WSGI server in production

## 👤 Author

- Name: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## 📄 License

This project is available under the MIT License. See the [LICENSE](LICENSE) file for more information.
