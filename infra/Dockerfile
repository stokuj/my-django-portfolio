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

# 4. Copy backend sources and generated CSS
COPY pyproject.toml uv.lock ./
COPY django ./django
COPY --from=css-builder /app/django/main/static/css/style.css /app/django/main/static/css/style.css

# 5. Install uv and install the locked dependencies, then the project itself
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
RUN uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt && \
    uv pip install --system --no-cache-dir -r /tmp/req.txt && \
    uv pip install --system --no-cache-dir --no-deps .

# 6. Create non-root runtime user and writable runtime directories
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app && \
    mkdir -p /app/staticfiles /app/media /app/django/celerybeat-schedule && \
    chown -R app:app /app/staticfiles /app/media /app/django/celerybeat-schedule /home/app

# 7. Set Python path
ENV PYTHONPATH="/app/django"

# 8. Run as non-root user
USER 10001:10001

# 9. Expose port
EXPOSE 8000
