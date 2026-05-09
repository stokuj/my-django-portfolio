.PHONY: dev-up dev-down dev-status prod-up prod-down prod-status verify

DEV_COMPOSE := docker compose -p my-django-portfolio-dev -f docker-compose.dev.yml
PROD_COMPOSE := docker compose -p my-django-portfolio-prod -f docker-compose.prod.yml

dev-up:
	uv run python scripts/ensure_env.py dev
	$(DEV_COMPOSE) up --build -d

dev-down:
	$(DEV_COMPOSE) down

dev-status:
	uv run python scripts/compose_status.py my-django-portfolio-dev

prod-up:
	uv run python scripts/ensure_env.py prod
	$(PROD_COMPOSE) up --build -d

prod-down:
	$(PROD_COMPOSE) down

prod-status:
	uv run python scripts/compose_status.py my-django-portfolio-prod

verify:
	npm run build:css:prod
	uv run python -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test
	uv run ruff check scripts tests
