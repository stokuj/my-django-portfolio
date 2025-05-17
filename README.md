
# 📝 Django Portfolio Blog

To repozytorium zawiera prosty blog stworzony w Django z wykorzystaniem PostgreSQL jako bazy danych. Aplikacja stanowi część mojego portfolio i ma na celu prezentację moich umiejętności w zakresie backendu, pracy z bazą danych oraz frameworkiem Django.

## 🔧 Technologie

- Python 3.x
- Django 5.1.7
- PostgreSQL
- Django Templates (HTML + Tailwind)
- Plugin DaisyUI do Tailwinda
- Gunicorn jako serwer WSGI
- Docker i Docker Compose
- WhiteNoise do obsługi plików statycznych
- CKEditor, TinyMCE i Summernote jako edytory tekstu
- Coverage do testów pokrycia kodu

## ⚙️ Funkcjonalności

- Każdy projekt posiada własną podstronę
- System statusów i tagów dla projektów
- Dynamiczne filtrowanie projektów
- PostgreSQL przechowuje projekty jako obiekty
- Licznik odwiedzin strony
- Responsywny interfejs użytkownika dzięki Tailwind CSS
- Obsługa plików multimedialnych
- Edytory tekstu sformatowanego (Rich Text)
- Optymalizacja zapytań bazy danych

## 🚀 Uruchomienie lokalne

### Krok 1: Klonowanie repozytorium

```powershell
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### Krok 2: Utwórz wirtualne środowisko i zainstaluj zależności

```powershell
python -m venv venv
venv\Scripts\Activate.ps1 # Windows PowerShell
# lub
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Krok 3: Skonfiguruj zmienne środowiskowe

Utwórz plik `.env` w głównym katalogu projektu z następującymi zmiennymi:

```
# Debug flag
DJANGO_DEBUG=True

# Secret key (wygeneruj nowy dla produkcji)
SECRET_KEY=twoj_tajny_klucz

# Konfiguracja bazy danych
DB_ENGINE=django.db.backends.postgresql
DB_NAME=twoja_baza
DB_USER=twoj_uzytkownik
DB_PASSWORD=twoje_haslo
DB_HOST=localhost
DB_PORT=5432

# Dozwolone hosty (oddzielone przecinkami)
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Krok 4: Skonfiguruj bazę danych PostgreSQL

1. Zainstaluj PostgreSQL jeśli jeszcze nie jest zainstalowany
2. Utwórz bazę danych o nazwie określonej w pliku `.env`

### Krok 5: Migracje i uruchomienie serwera

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

## 🐳 Uruchomienie z Docker

Projekt można również uruchomić za pomocą Docker Compose:

```powershell
docker-compose up --build
```

To polecenie:
- Skonfiguruje kontener z bazą danych PostgreSQL
- Zbuduje i uruchomi aplikację Django
- Zastosuje migracje
- Zbierze pliki statyczne
- Uruchomi serwer Gunicorn

Zmienne środowiskowe dla Dockera są zdefiniowane w pliku `docker-compose.yml`.

## 📁 Struktura projektu
    MY-DJANGO-PORTFOLIO/
    │
    ├── main/                      # Główna aplikacja zawierająca modele, widoki i szablony
    │   ├── migrations/            # Migracje bazy danych
    │   ├── static/                # Pliki statyczne (CSS, obrazy)
    │   ├── templates/             # Szablony HTML
    │   │   └── main/
    │   │       ├── blog/          # Każdy projekt ma własną podstronę
    │   │       ├── about.html     # Strona "O mnie"
    │   │       ├── home.html      # Strona główna
    │   │       └── projects.html  # Lista projektów
    │   │   └── base.html          # Bazowy szablon
    │   ├── __init__.py
    │   ├── admin.py               # Konfiguracja panelu administracyjnego
    │   ├── apps.py                # Konfiguracja aplikacji
    │   ├── context_processors.py  # Procesory kontekstu
    │   ├── models.py              # Modele danych
    │   ├── tests.py               # Testy
    │   ├── urls.py                # Konfiguracja URL
    │   └── views.py               # Widoki
    ├── media/                     # Pliki przesłane przez użytkowników
    ├── node_modules/              # Zależności Node.js
    ├── personal_portfolio/        # Główny katalog projektu
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── asgi.py                # Konfiguracja ASGI
    │   ├── settings.py            # Ustawienia projektu
    │   ├── urls.py                # Główne URL projektu
    │   └── wsgi.py                # Konfiguracja WSGI
    ├── staticfiles/               # Zebrane pliki statyczne dla produkcji
    ├── LICENSE                    # Licencja projektu
    ├── manage.py                  # Skrypt zarządzania Django
    ├── package-lock.json          # Zależności npm (lock)
    ├── package.json               # Konfiguracja npm
    ├── Procfile                   # Konfiguracja dla Heroku
    ├── README.md                  # Dokumentacja projektu
    ├── requirements.txt           # Zależności Pythona
    └── tailwind.config.js         # Konfiguracja Tailwind CSS

## 🧪 Testowanie

### Tworzenie testów

1. Utwórz pliki testowe w katalogu aplikacji `main`
2. Nazwij pliki testowe z prefiksem `test_` (np. `test_models.py`, `test_views.py`)

### Przykładowa struktura pliku testowego

Utwórz plik `main/test_models.py` z następującą zawartością:

```python
from django.test import TestCase
from django.utils import timezone
from .models import Project, Tag
import datetime

class ProjectModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Utwórz tag
        tag = Tag.objects.create(name="PYTHON")

        # Utwórz projekt
        project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished"
        )
        project.tags.add(tag)

    def test_project_title(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.title, "Test Project")

    def test_project_status(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.status, "finished")

    def test_project_tags(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.tags.count(), 1)
        self.assertEqual(project.tags.first().name, "PYTHON")
```

### Uruchamianie testów

```powershell
# Uruchom wszystkie testy
python manage.py test

# Uruchom testy dla konkretnej aplikacji
python manage.py test main

# Uruchom konkretną klasę testową
python manage.py test main.test_models.ProjectModelTest

# Uruchom konkretną metodę testową
python manage.py test main.test_models.ProjectModelTest.test_project_title
```

### Pokrycie testów

Aby zmierzyć pokrycie kodu testami, zainstaluj pakiet `coverage`:

```powershell
pip install coverage

# Uruchom testy z pomiarem pokrycia
coverage run --source='.' manage.py test

# Wygeneruj raport pokrycia
coverage report

# Wygeneruj raport HTML
coverage html
```

## 🔍 Dodatkowe informacje dla deweloperów

### Edytory tekstu sformatowanego

Projekt wykorzystuje kilka edytorów tekstu sformatowanego:
- CKEditor: Główny edytor (skonfigurowany w settings.py)
- TinyMCE: Alternatywny edytor
- Summernote: Kolejny alternatywny edytor

### Optymalizacja bazy danych

- Projekt wykorzystuje `prefetch_related` do optymalizacji zapytań z obiektami powiązanymi
- Rozważ dodanie indeksów dla często odpytywanych pól
- Projekt korzysta z pól specyficznych dla PostgreSQL, takich jak JSONField

### Obsługa plików statycznych

- WhiteNoise jest skonfigurowany do kompresji plików statycznych w produkcji
- Uruchom `python manage.py collectstatic` aby zebrać pliki statyczne do produkcji

### Wytyczne stylu kodu

1. Przestrzegaj PEP 8 dla stylu kodu Python
2. Używaj stylu kodowania Django dla kodu specyficznego dla Django
3. Dokumentuj swój kod za pomocą docstringów i komentarzy

### Frontend

1. Projekt wykorzystuje Tailwind CSS z pluginem DaisyUI do stylizacji
2. Konfiguracja Tailwind znajduje się w pliku `tailwind.config.js`
3. Pliki statyczne umieszczaj w katalogu `main/static/`

### Uwagi dotyczące wdrożenia

1. Gunicorn jest używany jako serwer WSGI w produkcji
2. WhiteNoise obsługuje pliki statyczne w produkcji
3. Docker jest skonfigurowany do wdrożenia w kontenerach

## 👤 Autor

- Imię i nazwisko: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## 📄 Licencja

Projekt dostępny na licencji MIT. Zobacz plik [LICENSE](LICENSE) po więcej informacji.

---

# 📝 Django Portfolio Blog

This repository contains a simple blog created with Django using PostgreSQL as the database. The application is part of my portfolio and aims to showcase my skills in backend development, database work, and the Django framework.

## 🔧 Technologies

- Python 3.x
- Django 5.1.7
- PostgreSQL
- Django Templates (HTML + Tailwind)
- DaisyUI plugin for Tailwind
- Gunicorn as WSGI server
- Docker and Docker Compose
- WhiteNoise for static files handling
- CKEditor, TinyMCE, and Summernote as rich text editors
- Coverage for code coverage testing

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

## 🚀 Local Setup

### Step 1: Clone the repository

```powershell
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### Step 2: Create a virtual environment and install dependencies

```powershell
python -m venv venv
venv\Scripts\Activate.ps1 # Windows PowerShell
# or
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Step 3: Configure environment variables

Create a `.env` file in the project root with the following variables:

```
# Debug flag
DJANGO_DEBUG=True

# Secret key (generate a new one for production)
SECRET_KEY=your_secret_key

# Database configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Allowed hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Step 4: Configure PostgreSQL database

1. Install PostgreSQL if not already installed
2. Create a database with the name specified in the `.env` file

### Step 5: Migrations and server startup

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

## 🐳 Running with Docker

The project can also be run using Docker Compose:

```powershell
docker-compose up --build
```

This command will:
- Configure a PostgreSQL database container
- Build and run the Django application
- Apply migrations
- Collect static files
- Start the Gunicorn server

Environment variables for Docker are defined in the `docker-compose.yml` file.

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

## 🧪 Testing

### Creating Tests

1. Create test files in the `main` app directory
2. Name test files with the prefix `test_` (e.g., `test_models.py`, `test_views.py`)

### Example Test File Structure

Create a file `main/test_models.py` with the following content:

```python
from django.test import TestCase
from django.utils import timezone
from .models import Project, Tag
import datetime

class ProjectModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a tag
        tag = Tag.objects.create(name="PYTHON")

        # Create a project
        project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished"
        )
        project.tags.add(tag)

    def test_project_title(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.title, "Test Project")

    def test_project_status(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.status, "finished")

    def test_project_tags(self):
        project = Project.objects.get(id=1)
        self.assertEqual(project.tags.count(), 1)
        self.assertEqual(project.tags.first().name, "PYTHON")
```

### Running Tests

```powershell
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test main

# Run a specific test class
python manage.py test main.test_models.ProjectModelTest

# Run a specific test method
python manage.py test main.test_models.ProjectModelTest.test_project_title
```

### Test Coverage

To measure test coverage, install the `coverage` package:

```powershell
pip install coverage

# Run tests with coverage measurement
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
```

## 🔍 Additional Developer Information

### Rich Text Editors

The project uses several rich text editors:
- CKEditor: Main editor (configured in settings.py)
- TinyMCE: Alternative editor
- Summernote: Another alternative editor

### Database Optimization

- The project uses `prefetch_related` to optimize queries with related objects
- Consider adding indexes for frequently queried fields
- The project uses PostgreSQL-specific fields such as JSONField

### Static Files Handling

- WhiteNoise is configured to compress static files in production
- Run `python manage.py collectstatic` to collect static files for production

### Code Style Guidelines

1. Follow PEP 8 for Python code style
2. Use Django's coding style for Django-specific code
3. Document your code with docstrings and comments

### Frontend

1. The project uses Tailwind CSS with the DaisyUI plugin for styling
2. Tailwind configuration is in the `tailwind.config.js` file
3. Place static files in the `main/static/` directory

### Deployment Notes

1. Gunicorn is used as the WSGI server in production
2. WhiteNoise handles static files in production
3. Docker is configured for containerized deployment

## 👤 Author

- Name: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## 📄 License

This project is available under the MIT License. See the [LICENSE](LICENSE) file for more information.
