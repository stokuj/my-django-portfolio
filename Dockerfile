# 1. Base Python image
FROM python:3.13-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# 4. Copy only files required to build and run backend
COPY pyproject.toml uv.lock ./
COPY django ./django

# 5. Install uv and use it to install dependencies
RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache-dir .

# 6. Make entrypoint script executable
RUN chmod +x /app/django/entrypoints/wait-for-db.sh

# 7. Set Python path
ENV PYTHONPATH="/app/django"

# 8. Expose port
EXPOSE 8000
