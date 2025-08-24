# Makefile for Docker Compose project management

# --- Variables ---
# Name of the main application service container
SERVICE_WEB = web

# --- Standard Commands ---

.PHONY: help
help: ## Display this help screen
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: start
start: ## Start containers in the background and rebuild image if needed
	docker compose up --build -d

.PHONY: stop
stop: ## Stop and remove containers
	docker compose down

.PHONY: restart
restart: stop start ## Restart the entire application
	@echo "Application has been restarted."

.PHONY: build
build: ## Rebuild container images without starting them
	docker compose build

.PHONY: logs
logs: ## Follow logs from all containers
	docker compose logs -f

.PHONY: clean
clean: ## Stop containers and remove volumes (WARNING: database data will be lost!)
	docker compose down -v --remove-orphans


# --- Django Specific Commands ---

.PHONY: superuser
superuser: ## Create a Django superuser
	docker compose exec $(SERVICE_WEB) python manage.py createsuperuser

.PHONY: shell
shell: ## Start an interactive BASH shell inside the application container
	docker compose exec $(SERVICE_WEB) bash

.PHONY: migrate
migrate: ## Run database migrations
	docker compose exec $(SERVICE_WEB) python manage.py migrate

.PHONY: makemigrations
makemigrations: ## Create new migration files
	docker compose exec $(SERVICE_WEB) python manage.py makemigrations