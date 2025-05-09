
# 📝 Django Portfolio Blog

To repozytorium zawiera prosty blog stworzony w Django z wykorzystaniem PostgreSQL jako bazy danych. Aplikacja stanowi część mojego portfolio i ma na celu prezentację moich umiejętności w zakresie backendu, pracy z bazą danych oraz frameworkiem Django.

## 🔧 Technologie

- Python 3.x
- Django 
- PostgreSQL
- Django Templates (HTML + Tailwind)
- Plugin DaisyUI do Tailwina
- Gunicorn 
- Docker (częsciowo używany)

## ⚙️ Funkcjonalności

- Każdy projekt posiada własną podstronę
- System statusy/ tagów dla projektów
- Dynamiczne filtrowanie projektów
- PostgreSQL przechowuje moje projekty jako obiekty

## 🚀 Uruchomienie lokalne

### Krok 1: Klonowanie repozytorium

```bash
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### Krok 2: Utwórz wirtualne środowisko i zainstaluj zależności

```bash
python -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\Activate.ps1 # Windows
pip install -r requirements.txt
```

### Krok 3: Skonfiguruj bazę danych PostgreSQL

Utwórz bazę danych i zaktualizuj ustawienia w `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'twoja_baza',
        'USER': 'twoj_uzytkownik',
        'PASSWORD': 'twoje_haslo',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Krok 4: Migracje i uruchomienie serwera
Jeżeli uruchamiany server lokalnie (nie przez Gunicorn)
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## 👤 Autor

- Imię i nazwisko: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## 📄 Licencja

Projekt dostępny na licencji MIT. Zobacz plik [LICENSE](LICENSE) po więcej informacji.
