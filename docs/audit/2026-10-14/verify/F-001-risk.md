# F-001 (risk lens): Deploy has no rollback tag, full downtime, no concurrency guard, not tied to built commit

- Verdict: CONFIRMED (facts hold), severity overstated, proposal partly harmful
- Confidence: high
- Adjusted severity: medium

## Facts verified at HEAD
- Only `:latest` is built/pushed: `infra/docker-compose.prod.yml:37,80,120` hardcode `ghcr.io/stokuj/my-django-portfolio:latest`; CI pushes via `docker compose ... push web` (`.github/workflows/docker-build-push.yml:77-80`). `IMAGE_NAME` exported at line 105 is unused by compose.
- `down --remove-orphans` then `up -d --force-recreate` (`docker-build-push.yml:108-109`) stops db/redis/caddy every release.
- `docker image prune -af` after up (`:112`) removes the previous image locally.
- Server does `git pull` of main HEAD (`:99-101`), not `github.sha`.
- No `concurrency:` anywhere in the workflow (`:1-12`).
- `migrate` runs on web start (`docker-compose.prod.yml:44`), no backup step. `web` has no healthcheck and no `restart:` policy (`:33-74`).

## Why severity is medium, not high
- No exploit, no data loss: `down` keeps named volumes (`docker-compose.prod.yml:185-191`). Migrate-without-backup is a latent risk, not an observed bug.
- Code runs from the image, so the server's `git pull` only affects compose/Caddyfile, not app code.
- "Older code deployed" needs build A to push `:latest` after build B. Possible but rare. Two overlapping `down`/`up` runs failing is the more likely outcome.
- Single-droplet personal portfolio; downtime is seconds to a minute per deploy.

## Risks of the proposed fix
1. `image prune --filter until=168h` brings back issue #57. The droplet has 10 GB, and about 2.2 GB of old images were measured reclaimable (`docs/superpowers/specs/2026-05-09-issue-57-disk-space-optimization-design.md:5,60,72`). Rollback does not need local images: `IMAGE_TAG=<prev sha> pull && up -d` fetches from GHCR. Keep `prune -af`.
2. `up -d --wait` gives false assurance. `web` has no healthcheck, so `--wait` only waits for "running", and web is "running" while `migrate` runs (`docker-compose.prod.yml:43-46`). Without a healthcheck it will not catch "web dies". Also web has no `restart:` policy, so a crash stays down.
3. Tests lock in the current script: `tests/test_operational_files.py:79-95` assert `down --remove-orphans`, `up -d --force-recreate`, and `image prune -af`. They must be updated in the same change. CI does not run `tests/` (`Makefile:33-39`, `.github/workflows/django.yml:46`), so the breakage would go unnoticed.
4. `down` was a deliberate choice (spec `:11,57`). Its stated reason (freeing ports held by other compose projects) is wrong, because `--remove-orphans` only touches the same project. `up -d --remove-orphans` is equivalent for this project, so dropping `down` is safe.
5. Pushing `:sha` together with `:latest` needs an explicit `docker tag` + `docker push` (or two compose pushes with different `IMAGE_TAG`). `compose push` pushes only the single `image:` value.
6. A `concurrency:` group on the deploy job alone does not stop the `:latest` push race in `build-and-push`. Put it at the workflow level.
7. pg_dump on a 10 GB disk needs a cap: overwrite one file, or keep the last N.

## Better proposal (in order, each shippable alone)
1. Workflow-level `concurrency: { group: deploy-prod, cancel-in-progress: false }`. (S)
2. Replace lines 108-109 with `up -d --remove-orphans` (no `down`, no `--force-recreate`). Compose then recreates only services whose image or config changed. Update `tests/test_operational_files.py:79-95`. (S)
3. Pre-deploy `docker compose ... exec -T db pg_dump -U "$DOCKER_DB_USER" "$DOCKER_DB_NAME" | gzip > ~/backups/pre-deploy.sql.gz` (one file, overwritten). (S)
4. Push `:${{ github.sha }}` as well, set `image: ghcr.io/stokuj/my-django-portfolio:${IMAGE_TAG:-latest}`, and deploy with `IMAGE_TAG=${{ github.sha }}`. Keep `image prune -af`, since rollback pulls the old SHA from GHCR. (S-M)
5. Only after adding a web `healthcheck` (and `restart: unless-stopped`), use `up -d --wait`. (S)
