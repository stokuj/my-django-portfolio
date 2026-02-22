# Architecture

## System Overview

The application is a Django-based portfolio/blog platform with asynchronous background processing.
Core runtime services are orchestrated with Docker Compose:

- `web`: Django app served by Gunicorn.
- `db`: PostgreSQL database.
- `redis`: message broker/result backend for Celery.
- `worker`: Celery worker for asynchronous jobs.
- `beat`: Celery beat scheduler for periodic jobs.
- `caddy`: reverse proxy and static/media serving.

## High-Level Diagram

```mermaid
flowchart LR
    U[User Browser] --> C[Caddy]
    C --> W[Gunicorn + Django Web]
    W --> P[(PostgreSQL)]
    W --> R[(Redis)]
    R --> WK[Celery Worker]
    B[Celery Beat] --> R
    WK --> P
    C --> S[(Static Files)]
    C --> M[(Media Files)]
```

## Backend Architecture

## Asynchronous Processing

Celery is used for jobs that should not block HTTP requests.

- Broker/backend: Redis (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`).
- Periodic schedule: `CELERY_BEAT_SCHEDULE` in `django/config/settings.py`.
- Notable periodic job: `main.tasks.sync_project_markdowns_task`.
- Task observability: `TaskExecutionStatus` and `TaskExecutionLog` store latest and historical run metadata.

### Async Flow Diagram

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Redis as Redis
    participant Worker as Celery Worker
    participant Django as Django Domain Logic
    participant DB as PostgreSQL

    Beat->>Redis: enqueue periodic task
    Redis->>Worker: deliver task
    Worker->>Django: execute task function
    Django->>DB: read/write state and logs
    Django-->>Worker: task result payload
```

## Static and Media Delivery

- Django collects static files into `/app/staticfiles`.
- User uploads are stored in `/app/media`.
- Docker named volumes share these directories with Caddy.
- Caddy serves static/media directly for efficiency.

## Security and Configuration

- Environment variables are loaded from `.env` via `django-environ`.
- `SECRET_KEY` is required; startup fails if missing.
- In non-debug mode, secure cookie and HTTPS settings are enabled.
- Allowed hosts and CSRF trusted origins are controlled by env vars.


