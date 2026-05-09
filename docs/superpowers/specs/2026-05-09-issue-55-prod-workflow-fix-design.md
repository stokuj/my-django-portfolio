# Prod Workflow Fix Design (Issue #55)

## Summary

Issue #53 introduced `docker-compose.prod.yml` inside `infra/` and a Makefile with explicit `-p` project names. The production project name was changed from `my_django_portfolio` (the original folder-based name) to `my-django-portfolio-prod`. This silently orphaned the existing Docker volumes containing PostgreSQL data, caused port conflicts during deployment, and left `make` targets that require Python/uv — unavailable on the DigitalOcean droplet.

This design reverts the production project name to the original `my_django_portfolio`, removes Python dependencies from production Makefile targets, and aligns the CI deploy script with the same project name.

## Goals

- Restore the production Compose project name to `my_django_portfolio` so existing volumes are reused.
- Make `make prod-up` and `make prod-status` run without Python or uv.
- Ensure the CI deploy workflow uses `-p my_django_portfolio` consistently.
- Keep `make dev-up`, `make dev-status`, and `make verify` unchanged (Python is available locally).
- Add regression tests for the production project name and shell-only targets.

## Non-Goals

- Changing the development project name (`my-django-portfolio-dev` stays).
- Removing Python from dev or verify targets.
- Restructuring the `infra/` directory layout.

## Proposed Changes

### Makefile

- `PROD_COMPOSE` variable: replace `-p my-django-portfolio-prod` with `-p my_django_portfolio`.
- `prod-up`: replace `uv run python infra/scripts/ensure_env.py prod` with a shell `test -f .env` guard.
- `prod-status`: replace `uv run python infra/scripts/compose_status.py my-django-portfolio-prod` with a direct `docker ps --format` command filtered by project label.
- `dev-*` targets and `verify` are unchanged.

### CI Deploy Workflow

- `.github/workflows/docker-build-push.yml` deploy script: add `-p my_django_portfolio` to the `docker compose pull` and `docker compose up` commands.

### Regression Tests

- `tests/test_operational_files.py`:
  - Update `test_makefile_passes_root_env_file_to_compose` to check `-p my_django_portfolio` (not `-p my-django-portfolio-prod`).
  - Update `test_makefile_uses_helper_scripts` to allow shell-only prod targets (the `ensure_env.py` import check is now dev-only).
  - Add `test_prod_up_uses_shell_env_guard` that asserts `prod-up` does NOT contain `python`.
  - Add `test_prod_status_uses_docker_ps_not_python` that asserts `prod-status` does NOT contain `python` but DOES contain `docker ps`.
  - Add `test_makefile_uses_original_prod_project_name` that asserts `my_django_portfolio` appears in `PROD_COMPOSE`.

## Environment File Behavior

- `prod-up` still fails when `.env` is missing, now using `test -f .env` instead of Python.
- `dev-up` still auto-creates `.env` from `.env.example` using Python (unchanged).

## Error Handling

- `make prod-up` without `.env`: shell exits with code 1 and prints a message.
- `make prod-status` with no matching containers: `docker ps` outputs only the table header.
- `make prod-down` with no matching containers: `docker compose down` exits 0 (idempotent).

## Testing Strategy

- Run `make verify` to confirm no regressions.
- Run `uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v`.
- Validate both compose files parse: `docker compose -f infra/docker-compose.dev.yml config` and `docker compose -f infra/docker-compose.prod.yml config`.
- On the droplet: `make prod-up` must reuse existing volumes and start without errors.

## Rationale

The original project name `my_django_portfolio` was derived from the repository directory name on the droplet. Changing it introduced a silent data migration problem that is more expensive to fix than to revert. Reverting the name keeps the existing volumes intact. Removing Python from production targets eliminates a non-obvious server dependency introduced in #53 and makes the Makefile self-documenting about what the droplet actually needs: Docker and a shell.
