# F-001 (worth lens): Deploy has no rollback tag, full downtime, no concurrency guard, not tied to built commit

**Verdict:** PARTIALLY CONFIRMED (problems real, proposal oversized and partly contradicts a documented decision)
**Confidence:** high
**Adjusted severity:** medium (was high)

## Verified at HEAD
- No `concurrency:` anywhere in `.github/workflows/docker-build-push.yml` (lines 1-11).
- Only `:latest` exists: `infra/docker-compose.prod.yml:37,80,120`; build/push at workflow `:77,80`.
- Server pulls branch tip, not `github.sha`: workflow `:99-101`.
- `down --remove-orphans` then `up -d --force-recreate`: workflow `:108-109` -> db/redis/caddy restart every deploy.
- `docker image prune -af` after up: workflow `:112` -> previous image removed locally.
- `migrate` runs in web command, no backup: compose `:44`. `web` has no `restart:` policy (compose `:33-74`), so a failed migrate leaves web down while `up -d` exits 0.

## Why not "high"
- `down` without `-v` keeps all named volumes (compose `:185-191`); no data-loss path. Single-maintainer portfolio, short downtime per deploy.
- Race needs two merges to main within one build window; both deploys pull `:latest`, so it usually converges to the newest image.

## Conflicts with deliberate decisions
- `down --remove-orphans` and `image prune -af` were chosen on purpose for a 10 GB droplet (old images ~2.2 GB, build cache ~1.1 GB): `docs/superpowers/specs/2026-05-09-issue-57-disk-space-optimization-design.md:9-13,55-60,77`, commit `1b830b4`.
- The proposed `prune --filter until=168h` keeps a week of images and reverses that decision. Not needed: rollback works by pulling `:<sha>` from GHCR, no local copy required.
- `tests/test_operational_files.py:81,85,89,93` assert `down --remove-orphans`, `image prune -af`, and `up -d --force-recreate`; they must be updated with any change.
- `pg_dump` before deploy is a separate concern (no backup exists at all); do not bundle it here.

## Better proposal (smallest diff)
1. Add at workflow top: `concurrency: { group: deploy-prod, cancel-in-progress: false }` (2 lines).
2. Replace `:108-109` with `up -d --remove-orphans --wait` (compose recreates changed services only; `--wait` fails the job if web exits). Keep `builder prune -af` and `image prune -af`.
3. Optional rollback: also tag/push `:${{ github.sha }}`, make compose `image: ghcr.io/stokuj/my-django-portfolio:${IMAGE_TAG:-latest}`, and on server `git checkout ${{ github.sha }}` + `export IMAGE_TAG=${{ github.sha }}`.
4. Update the four assertions in `tests/test_operational_files.py`.
Effort: S for 1-2+4, M with 3.
