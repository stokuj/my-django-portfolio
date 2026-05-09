# Disk Space Optimization Design (Issue #57)

## Summary

A 10 GB DigitalOcean droplet running this project accumulates disk usage from three preventable sources: unbounded container log growth, stale Docker images and build cache, and orphaned containers from previous failed deployments blocking cleanup. This design introduces log rotation, proactive image/cache pruning in the CI deploy script, and explicit orphan cleanup before bringing up new containers.

## Goals

- Cap container log growth with `json-file` rotation: `max-size: 10m`, `max-file: 3` on all six production services.
- Clean build cache and unused images during every successful deploy.
- Prevent port conflicts and disk waste from orphaned containers by running `docker compose down --remove-orphans` before `up`.
- Keep the `Makefile` and dev compose unchanged.

## Non-Goals

- Adding disk space monitoring or alerting.
- Changing the Docker storage driver or volume management.
- Modifying development compose (`docker-compose.dev.yml`).

## Proposed Changes

### 1. Log rotation in `infra/docker-compose.prod.yml`

Add a `logging` block to every service: `db`, `redis`, `web`, `worker`, `beat`, `caddy`.

```yaml
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

This limits each container to three 10 MB log files (30 MB per container). Total across six containers: approximately 180 MB maximum, compared to unbounded growth today.

### 2. CI deploy script cleanup

Replace the end of the deploy script in `.github/workflows/docker-build-push.yml`.

**Before:**
```yaml
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d --remove-orphans --force-recreate
            docker image prune -f
```

**After:**
```yaml
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml down --remove-orphans
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d --force-recreate
            docker builder prune -af
            docker image prune -af
```

Key differences:
- `down --remove-orphans` runs before `up`, ensuring any leftover containers (e.g. from other Compose projects like `infra-*`) are removed and their ports freed.
- `--remove-orphans` on `up` is removed — it is redundant after `down`.
- `docker builder prune -af` clears all Docker build cache, which was measured at ~1.1 GB on the droplet.
- `docker image prune -af` replaces `-f` (dangling only) — `-a` removes all unused images, including old versions of `:latest`.

### 3. No changes to dev compose or Makefile

Development targets and the development compose file are unchanged. Log rotation is not needed locally because dev containers are ephemeral and the development host is not disk-constrained.

## Expected Disk Impact

| Source | Before | After |
|--------|--------|-------|
| Container logs | unbounded growth | ≤ 180 MB total |
| Build cache | ~1.1 GB uncleaned | cleaned every deploy |
| Old images | ~2.2 GB reclaimable (measured) | cleaned every deploy |
| Orphaned containers | accumulate on failed deploy | removed before every `up` |

## Error Handling

- `docker compose down` is idempotent — it exits 0 even when no containers match the project name.
- `docker builder prune -af` and `docker image prune -af` are safe: they only remove unused objects, never active containers or their images.
- Log rotation is handled by the Docker daemon, not the container — no change to application behavior.

## Testing Strategy

- `make verify` must pass unchanged.
- `uv run python -m unittest tests.test_operational_files -v` must pass.
- Both compose files must parse: `docker compose -f infra/docker-compose.dev.yml config`, `docker compose -f infra/docker-compose.prod.yml config`.
- No new tests are required — the changes are configuration-only.

## Rationale

The three changes address the three independently measured disk consumers on the droplet: logs (unbounded), build cache (~1.1 GB), and old images (~2.2 GB). The orphan cleanup prevents a recurring failure mode where a prior failed deploy left containers that blocked ports and held references to volumes, breaking the next deploy. All changes are production-only; the development workflow is untouched.
