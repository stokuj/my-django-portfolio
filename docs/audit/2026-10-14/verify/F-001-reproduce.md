# F-001 (reproduce lens): Deploy has no rollback tag, full downtime, no concurrency guard, not tied to built commit

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (was high)

## Reasoning (verified at HEAD)
- Only `:latest` exists: image is hard-coded `ghcr.io/stokuj/my-django-portfolio:latest` (infra/docker-compose.prod.yml:37, 80, 120); CI pushes it via `compose push web` (.github/workflows/docker-build-push.yml:80). No SHA tag anywhere.
- Full stop/start: `down --remove-orphans` then `up -d --force-recreate` (docker-build-push.yml:108-109) stops and recreates db, redis, caddy too (compose:2, 22, 153).
- Previous image deleted: `docker image prune -af` (docker-build-push.yml:112) removes every image not used by a container, so the old image is gone after `up`.
- Not tied to the built commit: server runs `git pull origin main` (docker-build-push.yml:99-101), not `github.sha`; compose/Caddyfile come from whatever main is at that moment.
- No `concurrency:` key in the workflow (grep finds none; top-level is lines 1-10).
- migrate on start, no backup: compose:43-46; no pg_dump/backup in .github, infra, Makefile (grep empty).
- Silent failure: `up -d` without `--wait`; additionally `web` has NO `restart:` policy (compose:33-46, unlike worker:82 and beat:122), so if migrate fails web stays down and the job still passes.

## Why severity lowered
Single-maintainer portfolio: interleaving needs two merges within minutes, and the newer-run race usually ends with newer code. Downtime is short (db restart). `down` keeps named volumes, so no direct data loss; the real data-loss gap is "no DB backup at all", which is wider than this deploy step. Ops hygiene, not an active bug.

## Better proposal (smaller)
1. Add `concurrency: {group: deploy-prod, cancel-in-progress: false}` at workflow top.
2. Delete the `down --remove-orphans` line and drop `--force-recreate`; `up -d --wait` recreates only changed services (web/worker/beat).
3. Add `restart: unless-stopped` to `web` so `--wait`/restart behavior is meaningful.
4. Server: `git fetch origin && git checkout --detach ${{ github.sha }}` instead of pull.
5. Push `:${{ github.sha }}` next to `:latest`; compose `image: ghcr.io/stokuj/my-django-portfolio:${IMAGE_TAG:-latest}`; prune with `--filter until=168h` to keep rollback images.
6. pg_dump before `up`: optional, better solved as a separate scheduled backup finding.
