# 1. Build Tailwind CSS artifact
FROM node:22-slim AS css-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY django ./django
RUN npm run build:css:prod

# 2. Base Python image
FROM python:3.13-slim

# 3. Set working directory
WORKDIR /app

# 4. Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# 5. Copy backend sources and generated CSS
COPY pyproject.toml uv.lock ./
COPY django ./django
COPY --from=css-builder /app/django/main/static/css/style.css /app/django/main/static/css/style.css

# 6. Install uv and use it to install dependencies
RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache-dir .

# 7. Make entrypoint script executable
RUN chmod +x /app/django/entrypoints/wait-for-db.sh

# 8. Create non-root runtime user and writable runtime directories
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app && \
    mkdir -p /app/staticfiles /app/media /app/django/celerybeat-schedule && \
    chown -R app:app /app /home/app

# 9. Set Python path
ENV PYTHONPATH="/app/django"

# 10. Run as non-root user
USER 10001:10001

# 11. Expose port
EXPOSE 8000
