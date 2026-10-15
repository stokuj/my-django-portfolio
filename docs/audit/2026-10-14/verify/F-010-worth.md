# F-010 — No backups of Postgres or media volume (worth lens)

**Verdict:** CONFIRMED (with adjusted severity and a simpler fix)
**Confidence:** medium
**Adjusted severity:** medium

## Reasoning
- `infra/docker-compose.prod.yml:186` (`postgres_data`) and `:188` (`media_volume`) are plain local named volumes. No backup service, script, Makefile target, or CI step exists in the repo (grep for backup/pg_dump/rclone/restore finds none outside docs/audit).
- The only `pg_dump` in the repo is a one-off manual step for the PG13->16 upgrade (`docs/superpowers/specs/2026-05-14-codebase-audit-design.md:120`), which was later reverted (commit `b8da60e`). Not a backup policy, and nothing documents a deliberate "no backups" decision.
- Data that cannot be regenerated: `Project` rows and admin-uploaded `thumbnail` (`django/main/models.py:59`), `Tag`, `PortfolioProfile` (`:169`), `PageView` counts (`:106`). Regenerable: `HeatmapSnapshot` (`:223`, hourly Celery task), task logs, and README markdown in `blog_markdown/` (`:60`, re-synced from GitHub).
- So the gap is real, but "high" overstates it. This is a low-traffic personal portfolio with a small, hand-entered dataset that can mostly be rebuilt from GitHub and admin input. No bug or exploit exists today; the risk is losing the droplet or its disk.
- Caveat: droplet-level DigitalOcean Backups/Snapshots are set outside the repo and cannot be checked from code. If they are on, the finding is mostly moot.

## Better proposal (smallest diff)
1. Turn on DigitalOcean droplet Backups (one toggle, zero code). They snapshot the whole disk, including both Docker volumes, and store the copies off the droplet. Postgres recovers a crash-consistent image through WAL replay.
2. Optional, only if you want logical dumps: a single host cron line, `docker compose -f infra/docker-compose.prod.yml exec -T db pg_dump -Fc ... > ~/backups/db_$(date +%F).dump` plus `find -mtime +14 -delete`, and a short restore note in `docs/implementation.md`. Leave out rclone/Spaces unless step 1 is rejected, because a dump on the same disk does not survive losing the droplet.

Skipped: media tar plus rclone pipeline. Add it if droplet backups are off and thumbnails become numerous.
