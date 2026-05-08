# Dev/Prod Compose Split and Makefile Workflow Design

## Summary

This design introduces a clear operational split between local development and production for the Django portfolio project. The current repository uses a single `docker-compose.yml`, manual `.env` preparation, and several disconnected verification commands. The new design adds a Makefile-based workflow, renames the current compose file to `docker-compose.prod.yml`, adds a dedicated `docker-compose.dev.yml`, and standardizes project verification behind `make verify`.

The implementation must happen on a dedicated feature branch, not on `main` or `master`.

## Goals

- Provide simple developer entrypoints through `make`.
- Separate development and production container orchestration.
- Allow `make dev-up` to bootstrap `.env` from `.env.example` when missing.
- Require an existing `.env` for `make prod-up`.
- Add one command that runs the full verification suite, including linting.
- Keep local development simpler by removing Caddy from the dev stack.

## Non-Goals

- Re-architect container images.
- Replace Docker Compose with another orchestrator.
- Introduce environment templating beyond `.env.example` to `.env` copy behavior.
- Redesign CI beyond changes required to follow the new compose file naming.

## Current State

The repository currently has:

- one root `docker-compose.yml` used as the main operational compose file,
- no root `Makefile`,
- manual `.env` preparation documented in `README.md`,
- verification commands split across README and GitHub Actions,
- no Ruff integration,
- production concerns such as Caddy mixed into the only compose file.

This leads to higher setup friction, inconsistent operator behavior, and a weak separation between local and production workflows.

## Proposed File Layout

- `docker-compose.prod.yml`
  - renamed version of the current root compose file,
  - remains the production-oriented stack.
- `docker-compose.dev.yml`
  - new local development compose file,
  - excludes Caddy,
  - exposes Django directly.
- `Makefile`
  - primary interface for local and production operations.
- `README.md`
  - updated to document the new workflow.
- `.github/workflows/*.yml`
  - updated only where the old compose filename is referenced.
- `pyproject.toml`
  - updated to include Ruff configuration and dependency declaration.

## Architecture

### Production Compose

`docker-compose.prod.yml` will be the direct successor to the existing `docker-compose.yml`.

It will keep the full production stack:

- `db`
- `redis`
- `web`
- `worker`
- `beat`
- `caddy`

This file remains responsible for the deployment-oriented topology, including reverse proxying and shared static/media serving.

### Development Compose

`docker-compose.dev.yml` will define a development-oriented stack with these services:

- `db`
- `redis`
- `web`
- `worker`
- `beat`

Caddy is intentionally excluded from development to reduce local complexity and make debugging more direct. The `web` service will expose Django directly on port `8000`, allowing the browser to connect without a reverse proxy.

The development workflow is still container-first: the full application stack runs in Docker, not partially on the host.

## Makefile Interface

The Makefile becomes the canonical operator interface.

### Development Commands

- `make dev-up`
  - if `.env` does not exist, copy `.env.example` to `.env`,
  - then run the development compose stack.
- `make dev-status`
  - show a readable table built from `docker ps --format`,
  - include at least container name, status, image, and ports,
  - filter results to dev containers only.
- `make dev-down`
  - stop the development stack.

### Production Commands

- `make prod-up`
  - fail immediately if `.env` does not exist,
  - do not copy `.env.example`,
  - start the production stack.
- `make prod-status`
  - show a readable table similar to `dev-status`, but filtered to production containers.
- `make prod-down`
  - stop the production stack.

### Verification Command

- `make verify`
  - run the complete local verification suite,
  - stop on the first failure,
  - return a non-zero exit code when any check fails.

## Verification Scope

`make verify` must cover the checks the project already relies on, plus Ruff linting.

The expected verification steps are:

- `uv run python django/manage.py check`
- `uv run python django/manage.py makemigrations --check --dry-run`
- `uv run python django/manage.py test`
- `python -m compileall django`
- `npm run build:css:prod`
- `uv run ruff check .`

This command is intended to be the single local quality gate for backend validity, migration consistency, test coverage, CSS build health, syntax compilation, and linting.

## Environment File Behavior

### Development

Development prioritizes fast startup.

Behavior:

- if `.env` is missing, create it from `.env.example`,
- continue startup after the copy,
- fail only if the source `.env.example` is missing or Docker startup fails.

This keeps local onboarding simple while still preserving the editable `.env` file for follow-up adjustments.

### Production

Production prioritizes explicit configuration.

Behavior:

- if `.env` is missing, fail before starting any container,
- do not create `.env` automatically,
- require operators to prepare the final environment explicitly.

This avoids accidental production startup with placeholder configuration.

## Status Output Design

The user requested prettier status output than the default `docker compose ps` format.

Both `make dev-status` and `make prod-status` should therefore use a table-oriented `docker ps --format` view, similar to:

```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

The implementation should extend this with ports where useful and filter by the compose project or labels so that unrelated local containers are not shown.

## Documentation Changes

The new workflow must be reflected in `README.md`.

Documentation updates should include:

- how to start development with `make dev-up`,
- how to stop and inspect both environments,
- how `.env` behaves in dev versus prod,
- how to run `make verify`,
- updated references from `docker-compose.yml` to `docker-compose.prod.yml` where applicable.

## CI and Workflow Impact

Any GitHub workflow that assumes the root production compose file is named `docker-compose.yml` must be updated to `docker-compose.prod.yml`.

This change should remain minimal:

- keep workflow behavior the same where possible,
- only update file references and related documentation.

## Error Handling Expectations

- `make dev-up` fails if `.env.example` is missing.
- `make prod-up` fails if `.env` is missing.
- `make verify` stops at the first failing verification step.
- status commands should succeed even if no matching containers exist, but clearly show an empty result.

## Testing Strategy

The implementation will be considered complete when these checks pass:

- `make dev-up`
- `make dev-status`
- `make dev-down`
- `make prod-up` without `.env` fails early with a clear message
- `make verify`

Additional validation should confirm that:

- development does not depend on Caddy,
- production still uses the full stack,
- renamed compose references are aligned in documentation and CI.

## Rationale

This design deliberately favors a minimal and explicit structure over a more abstract shared-compose hierarchy. The repository is small enough that introducing separate dev and prod compose files is easier to understand and maintain than creating a layered base/override system.

The Makefile centralizes routine operations, reduces command memorization, and gives the project a stable operator interface. Splitting dev and prod also reduces local friction while keeping production startup strict and intentional.
