# gap-human-docs-drift

Scope: README.md, docs/architecture.md, docs/frontend.md, .env.example, .github/ISSUE_TEMPLATE/*.md checked against Makefile, infra/*, settings.py, tasks.py, urls.py, package.json, pyproject.toml at HEAD (dev). Skipped CLAUDE.md (F-019), docs/superpowers (F-043), docs/implementation.md (F-098), beat entry name (F-063).

Env var cross-check: every var settings.py reads (SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DB_*, GITHUB_HEATMAP_TOKEN, HEATMAP_CACHE_TTL_MINUTES, CELERY_BROKER_URL, CELERY_RESULT_BACKEND) is in .env.example. Reverse direction: only IMAGE_NAME is unused (finding 5). Issue templates are stock GitHub boilerplate with no project claims to verify, so no findings there.

## 1. `make verify` prerequisites omit npm install
- Severity: low | Category: docs | Effort: S
- File: README.md:143
- Problem: README says `make verify` only needs `uv sync --extra dev`. The first step is `npm run build:css:prod` (Makefile:34), and input.css loads `@plugin "daisyui"` (django/main/static/src/css/input.css:5), which must be in node_modules. CI runs `npm ci` before `make verify` (.github/workflows/django.yml:37,46).
- Proposal: change it to "expects `uv sync --extra dev` and `npm install`".
- Risk: none.

## 2. Periodic jobs listed incompletely
- Severity: low | Category: docs | Effort: S
- File: docs/architecture.md:146; README.md:43-44
- Problem: the docs name only `sync_project_markdowns_task`. CELERY_BEAT_SCHEDULE has three entries: the hourly heatmap refresh, the 2-hourly markdown sync and the daily 06:00 `check_disk_usage_task` (django/config/settings.py:214-227, django/main/tasks.py:201). The disk check is not mentioned anywhere in the human docs.
- Proposal: list all three tasks with their schedules in architecture.md, under Asynchronous Processing.
- Risk: none.

## 3. Service list describes prod only
- Severity: low | Category: docs | Effort: S
- File: docs/architecture.md:6-13
- Problem: the docs say "Core runtime services are orchestrated with Docker Compose" and include `caddy`, with `web` "served by Gunicorn". The dev compose has no caddy service and runs `manage.py runserver` (infra/docker-compose.dev.yml:32-34). Only prod uses Gunicorn and Caddy (infra/docker-compose.prod.yml:46,153).
- Proposal: add one line: "Dev compose omits Caddy; web uses runserver on 127.0.0.1:8000."
- Risk: none.

## 4. About page called the "main landing page"
- Severity: low | Category: docs | Effort: S
- File: README.md:67
- Problem: the root URL maps to `views.home` (django/main/urls.py:5) and renders pages/home.html. The About page is `/about/` (django/main/urls.py:7).
- Proposal: drop "The main landing page" from the About caption.
- Risk: none.

## 5. IMAGE_NAME in .env.example is unused
- Severity: low | Category: docs | Effort: S
- File: .env.example:30
- Problem: no compose file, Makefile or settings reads IMAGE_NAME. The prod compose hardcodes `ghcr.io/stokuj/my-django-portfolio:latest` (infra/docker-compose.prod.yml:37,80,120), and the workflow sets its own IMAGE_NAME inline (.github/workflows/docker-build-push.yml:10). Users may think changing it has an effect. (F-055 covers the workflow side.)
- Proposal: remove the line, or use `${IMAGE_NAME:-ghcr.io/stokuj/my-django-portfolio:latest}` in the prod compose.
- Risk: none if removed.

## 6. Python version prerequisite too loose
- Severity: low | Category: docs | Effort: S
- File: README.md:106
- Problem: README says "Python 3.13+", but pyproject.toml:5 pins `requires-python = ">=3.13,<3.14"`, so 3.14 is rejected by uv.
- Proposal: change it to "Python 3.13".
- Risk: none.

## 7. Frontend diagram misses edges and templates
- Severity: low | Category: docs | Effort: S
- File: docs/frontend.md:42,46-71
- Problem:
  - errors/404.html:7 and errors/500.html:7 include components/hero_section.html, but the diagram has no Errors -> Hero edge.
  - projects/detail.html:28,45 include blog_sidebar_cards.html, which does not match the `blog_*_sidebar.html` node (frontend.md:42).
  - The diagram leaves out the per-page hero content templates (components/hero/*_content.html, passed in via hero_content_template) and the local static/js/mathjax-config.js (projects/detail.html:51).
- Proposal: add the Errors -> Hero edge, name both sidebar partials, and add a Hero -> hero/*_content.html node.
- Risk: none.
