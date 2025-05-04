# Używamy obrazu Pythona jako podstawy
FROM python:3.13.3

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy plik requirements.txt do kontenera
COPY requirements.txt /app/

# Instalujemy zależności
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą aplikację do kontenera
COPY . /app/

# Expose port, na którym działa Django
EXPOSE 8000

# Ustawiamy domyślną komendę do uruchomienia aplikacji
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
