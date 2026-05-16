.PHONY: dev-up dev-down dev-status prod-up prod-down prod-status verify

DEV_COMPOSE := docker compose --env-file .env -p my-django-portfolio-dev -f infra/docker-compose.dev.yml
PROD_COMPOSE := docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml

dev-up:
	uv run python infra/scripts/ensure_env.py dev
	$(DEV_COMPOSE) up --build -d
	@echo ""
	@echo "  Frontend:  http://localhost:8000"
	@echo "  Admin:     http://localhost:8000/admin"
	@echo "  DB:        localhost:15432"
	@echo ""

dev-down:
	$(DEV_COMPOSE) down

dev-status:
	uv run python infra/scripts/compose_status.py my-django-portfolio-dev

prod-up:
	@test -f .env || { echo "Error: .env file is missing. Create it first."; exit 1; }
	$(PROD_COMPOSE) up -d

prod-down:
	$(PROD_COMPOSE) down

prod-status:
	@docker ps -a \
		--filter "label=com.docker.compose.project=my_django_portfolio" \
		--format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

verify:
	npm run build:css:prod
	uv run python -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test
	uv run ruff check infra/scripts tests
