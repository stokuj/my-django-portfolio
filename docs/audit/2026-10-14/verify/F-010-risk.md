# F-010 — No backups of Postgres or media volume (risk lens)

**Verdict:** CONFIRMED
**Confidence:** high (repo); the one unknown is whether DigitalOcean droplet backups are switched on in the DO console, which the repo cannot show.
**Adjusted severity:** high (unchanged)

## Evidence
- `infra/docker-compose.prod.yml:13` mounts `postgres_data`. `:51`, `:90` and `:163` mount `media_volume`. `:185-188` declares them as plain local named volumes with no driver and no bind to off-host storage.
- No backup tooling exists anywhere. `rg -i 'backup|pg_dump|rclone|restore'` finds nothing in `infra/`, `.github/`, `Makefile`, README or `docs/architecture.md`. `infra/scripts/` contains only `compose_status.py` and `ensure_env.py`.
- `infra/docker-compose.prod.yml:44` runs `python manage.py migrate` on every container start. `.github/workflows/docker-build-push.yml:107-109` runs `down` and then `up --force-recreate` on every merge to main. So each deploy applies migrations to prod with no dump beforehand. A bad migration cannot be rolled back.
- Some of the data cannot be rebuilt. `Project.thumbnail` and `markdown_file` (`django/main/models.py:59-61`) are admin uploads in `media/`. `Project`, `Tag` and `PortfolioProfile` hold hand-entered content. `PageView` holds history. Only `HeatmapSnapshot` and the synced markdown can be fetched again.
- Commit `b8da60e` deferred the "PostgreSQL 16 -> 13 (migration deferred)" upgrade. A major-version upgrade needs a `pg_dump` anyway, so backups are a prerequisite for it.

## Why severity stays high
This is not exploitable. However, the rubric calls data loss critical, and here a single disk failure, a droplet deletion or a destructive migration loses data permanently. The site is a small personal portfolio, so high fits better than critical. If DO droplet backups turn out to be on, drop to medium (only RPO and logical-restore gaps remain).

## Risks when applying the proposed fix
1. **Compose project name.** Deploy runs with `-p my_django_portfolio --env-file .env` (`docker-build-push.yml:107`). A cron line like `docker compose exec db ...` without the same `-p` and `-f infra/docker-compose.prod.yml` resolves to a different project and fails silently. Cron also has no TTY, so it needs `exec -T`.
2. **Volume names are prefixed.** The real volume is `my_django_portfolio_media_volume`, not `media_volume`. Tarring the wrong name produces an empty archive and the job still reports success.
3. **Ownership on restore.** Containers run as uid `10001`. Use `tar --numeric-owner -p` for the media archive, or a restore leaves files the app cannot write.
4. **Disk pressure.** Keeping 14 local dumps on the same droplet trips the daily disk check (`django/config/settings.py:224`, `check_disk_usage_task`; thresholds in `django/main/views.py:248-250`). It also does not protect against disk loss. Keep only 1-2 copies locally and keep retention on the off-host side.
5. **Sensitive contents.** The dump includes `auth_user` password hashes and `django_session`. The off-host bucket must be private, and ideally the dump is encrypted (`rclone crypt` or `age`). Keep the rclone/Spaces credentials out of the repo.
6. **Silent failure.** A cron job that is never monitored gives false confidence. Add a check that the latest dump is less than about 26 h old and non-empty, for example as a Celery-beat task next to `check_disk_usage_task`, or use a healthcheck ping.
7. **Version coupling.** A `pg_dump -Fc` from PG13 restores into PG13 or newer, so it is safe for the planned upgrade. Run `pg_dump` inside the `db` container so client and server versions match.

## Better proposal
- First, with no code: enable DigitalOcean droplet backups (daily). They cover both volumes off-host. Postgres recovers from a crash-consistent snapshot.
- Then: a small `infra/scripts/backup.sh` run by host cron. It runs `docker compose -p my_django_portfolio -f infra/docker-compose.prod.yml exec -T db pg_dump -Fc -U "$DOCKER_DB_USER" "$DOCKER_DB_NAME"`, then `docker run --rm -v my_django_portfolio_media_volume:/m alpine tar --numeric-owner -czf - -C /m .`, then `rclone copy` to a private Spaces bucket with lifecycle retention.
- Optional: run the same dump step in the deploy script before `down` (`docker-build-push.yml:108`), so every migration has a restore point.
- Write a one-page restore drill and run it once.
- Effort: S for droplet backups plus the script. M if it includes off-host encryption, a freshness check and a tested restore.
