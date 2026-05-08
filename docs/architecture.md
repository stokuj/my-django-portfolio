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

The heatmap feature is implemented inside Django and fetches GitHub data directly.

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
    W --> G[GitHub REST + GraphQL APIs]
    C --> S[(Static Files)]
    C --> M[(Media Files)]
```

## Backend Architecture

### Django Layering

- `django/config/`: project configuration (`settings.py`, `urls.py`, `celery.py`).
- `django/main/models.py`: domain entities, including projects and task execution status/logging.
- `django/main/views.py`: request handling and template rendering.
- `django/main/tasks.py`: asynchronous and scheduled task execution.
- `django/main/markdown_sync.py` and `django/main/heatmap.py`: integration and domain helpers.

# ERD (Django Models)

```mermaid
erDiagram
    PAGEVIEW {
        int id PK
        int count
    }

    TASK_EXECUTION_STATUS {
        int id PK
        string task_name UK
        string last_status
        datetime last_run_at
        datetime last_success_at
        datetime last_failure_at
        int last_total
        int last_updated
        int last_failed
        text last_error
    }

    TASK_EXECUTION_LOG {
        int id PK
        string task_name
        string last_status
        datetime last_run_at
        datetime last_success_at
        datetime last_failure_at
        int last_total
        int last_updated
        int last_failed
        text last_error
        datetime created_at
    }

    PORTFOLIO_PROFILE {
        int id PK
        string site_name
        string full_name
        string role_line
        string specialization_line
        string home_intro
        string about_intro
        json core_stack
        json current_learning
        string current_learning_summary
        json interests
        string email
        string github_url
        string linkedin_url
        boolean is_active
    }

    HEATMAP_SNAPSHOT {
        int id PK
        string key UK
        json payload
        string username
        int total
        int weeks_count
        datetime fetched_at
        text last_error
    }
```
```mermaid
erDiagram
    TAG {
        int id PK
        string name UK
    }

    PROJECT {
        int id PK
        string title
        string thumbnail
        string markdown_file
        json tech_stack
        json tools_libraries
        string short_description
        date date
        boolean blog
        string blog_url
        string github_url
        string status
    }
    PROJECT }o--o{ TAG : tags
```
### Request Flow

1. A request reaches Caddy.
2. Caddy forwards dynamic routes to Gunicorn/Django.
3. Django middleware runs (`SecurityMiddleware`, sessions, visitor counter, CSRF, auth, etc.).
4. Views read or write data through Django ORM.
5. Templates render HTML using shared context processors.
6. The response is returned through Caddy.

## Asynchronous Processing

Celery is used for jobs that should not block HTTP requests.

- Broker/backend: Redis (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`).
- Periodic schedule: `CELERY_BEAT_SCHEDULE` in `django/config/settings.py`.
- Notable periodic job: `main.tasks.sync_project_markdowns_task`.
- Task observability: `TaskExecutionStatus` and `TaskExecutionLog` store latest and historical run metadata.

## Direct GitHub Heatmap Integration

The project fetches GitHub contribution heatmap data directly from Django.

- The GitHub bearer token is configured with `GITHUB_HEATMAP_TOKEN`.
- Django calls GitHub REST `/user` to resolve the configured account and GitHub GraphQL to fetch contribution days.
- Data is normalized and persisted in `HeatmapSnapshot`.
- On token or upstream errors, Django returns safe fallback messages and keeps the last valid snapshot.

### Async Flow Diagram

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Redis as Redis
    participant Worker as Celery Worker
    participant Django as Django Domain Logic
    participant GitHub as GitHub APIs
    participant DB as PostgreSQL

    Beat->>Redis: enqueue periodic task
    Redis->>Worker: deliver task
    Worker->>Django: execute task function
    Django->>GitHub: GET /user + GraphQL contributionCalendar
    GitHub-->>Django: contribution payload / error
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

## Extensibility Notes

- Keep views thin; move business logic into helpers/services/tasks.
- Keep task payloads and return structures stable.
- Add new periodic jobs through `CELERY_BEAT_SCHEDULE` and explicit task logging.
