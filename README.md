
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
## Struktura projektu
    MY-DJANGO-PORTFOLIO/
    │
    ├── main/
    │   ├── migrations/
    │   ├── static/...{css i images}
    │   ├── templates/
    │   │   └── main/
    │   │       ├── blog/{każdy projekt ma podstrone}
    │   │       ├── about.html
    │   │       ├── home.html
    │   │       └── projects.html
    │   │   └── base.html
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── context_processors.py
    │   ├── models.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    ├── media/
    ├── node_modules/
    ├── personal_portfolio/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── staticfiles/
    ├── LICENSE
    ├── manage.py
    ├── package-lock.json
    ├── package.json
    ├── Procfile
    ├── README.md
    ├── requirements.txt
    └── tailwind.config.js

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

### Obsługa plików statycznych

- WhiteNoise jest skonfigurowany do kompresji plików statycznych w produkcji
- Uruchom `python manage.py collectstatic` aby zebrać pliki statyczne do produkcji

### Wytyczne stylu kodu

1. Przestrzegaj PEP 8 dla stylu kodu Python
2. Używaj stylu kodowania Django dla kodu specyficznego dla Django
3. Dokumentuj swój kod za pomocą docstringów i komentarzy

## 👤 Autor

- Imię i nazwisko: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## 📄 Licencja

Projekt dostępny na licencji MIT. Zobacz plik [LICENSE](LICENSE) po więcej informacji.
