# F-010 - No backups of Postgres or media volume (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high (for the repo); out-of-repo DO droplet backups cannot be ruled out
**Adjusted severity:** medium

## Reasoning
- `infra/docker-compose.prod.yml:185-188` declares `postgres_data`, `staticfiles_volume`, `media_volume` as plain local named volumes (no driver/external storage).
- `infra/docker-compose.prod.yml:13` mounts `postgres_data` for `db`; `:51`, `:90`, `:163` mount `media_volume` for web/worker/caddy.
- No backup mechanism anywhere in the repo: `rg -i "backup|pg_dump|rclone|spaces"` over README.md, CLAUDE.md, docs/implementation.md, docs/architecture.md, infra/, .github/, Makefile returns nothing. `infra/scripts/` holds only `compose_status.py` and `ensure_env.py`.
- Deploy (`.github/workflows/docker-build-push.yml:107-109`) does pull / down / up with no dump step, and `web` runs `manage.py migrate` on every start (`infra/docker-compose.prod.yml:44`), so a bad migration hits prod data with no restore point.

## Why medium, not high
- Part of the data is reproducible: `media/blog_markdown/` is re-synced from GitHub by `sync_project_markdowns_task`, and `HeatmapSnapshot` is re-fetched from GitHub.
- What is truly at risk: admin-entered `Project`/`Tag`/`PortfolioProfile` rows, `Project.thumbnail` uploads (`django/main/models.py:59`), `PageView` counts, task logs. Small, personal-portfolio data, re-enterable by hand.
- DigitalOcean droplet backups may be enabled in the DO console; that is not visible from code and should be checked before doing work.

## Better proposal
1. Check the DO console first; if droplet backups are off, turn them on (zero code, covers volumes and host).
2. Add one line to the deploy script before `down`: `docker compose ... exec -T db pg_dump -Fc -U "$DOCKER_DB_USER" "$DOCKER_DB_NAME" > ~/backups/pre-deploy-$(date +%F-%H%M).dump` plus `find ~/backups -mtime +14 -delete`. This gives a restore point before every auto-migrate.
3. Media: only `thumbnails/` needs backup (markdown is re-synced). Skip a separate tar unless droplet backups are off.
4. Off-host copy (rclone to Spaces) only if droplet backups are not used.
