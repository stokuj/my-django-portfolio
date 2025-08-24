# 1. Base Python image
FROM python:3.13-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies + uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev postgresql-client curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# 4. Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# 5. Copy project files (uv needs pyproject.toml)
COPY pyproject.toml uv.lock* ./
COPY . .

# 6. Install dependencies via uv
RUN uv sync --frozen

# Make entrypoint script executable
RUN chmod +x /app/entrypoints/wait-for-db.sh

#Set Python path to use uv virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# 7. Expose port
EXPOSE 8000

# 8. Default command with uv
CMD ["uv", "run", "gunicorn", "personal_portfolio.wsgi:application", "--bind", "0.0.0.0:8000"]