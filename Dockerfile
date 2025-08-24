# 1. Base Python image
FROM python:3.13-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# 4. Copy requirements file
# Copy only dependency files first to leverage Docker cache
COPY requirements.txt ./

# 5. Install dependencies via pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# 6. Make entrypoint script executable
RUN chmod +x /app/entrypoints/wait-for-db.sh

# 7. Set Python path
ENV PYTHONPATH="/app"

# 8. Expose port
EXPOSE 8000
