# 1. Bazowy obraz Pythona
FROM python:3.11-slim

# 2. Ustawienie katalogu roboczego
WORKDIR /app

# 3. Zainstaluj systemowe zależności (jeśli potrzebne, np. psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 4. Skopiuj i zainstaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Skopiuj resztę kodu
COPY . .

# 6. Otwórz port (domyślnie Django na 8000)
EXPOSE 8000

# 7. Komenda domyślna
CMD ["gunicorn", "personal_portfolio.wsgi:application", "--bind", "0.0.0.0:8000"]
