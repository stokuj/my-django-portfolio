# ops

Scope: Celery tasks/beat, logging, health checks, backups, disk monitoring, deploy/rollback, PostgreSQL 13 upgrade plan (HEAD of `dev`, 4416049).

## 1. PostgreSQL 13 is EOL: migration plan to 17 (dump/restore)
- Severity: high | Category: ops | Effort: M
- File: infra/docker-compose.prod.yml:3 (also :13, infra/docker-compose.dev.yml:3)
- Problem: `image: postgres:13`; PG 13 went EOL in Nov 2025, so it no longer gets security fixes. The bump to 16 (667e27f) was reverted in b8da60e because it only changed the image tag. A new major cannot start on an old data dir ("database files are incompatible with server"), so `db` would crash-loop on the existing `postgres_data` volume. Staying on 13 also blocks Django 5.2 LTS, which needs PG >= 14 (current pin `django==5.1.15`, pyproject.toml:11). CI runs on SQLite only, so no CI job runs against PG.
- Proposal (target `postgres:17`: same `/var/lib/postgresql/data` mount, supported to Nov 2029, safe for Django 5.1 and 5.2. For 18, the mount must change to `/var/lib/postgresql`, because the 18+ image uses `PGDATA=/var/lib/postgresql/18/docker` and refuses old-layout mounts):
  0. Prep PR (do not merge yet): prod+dev compose `image: postgres:17`. Prod `db` volume becomes `postgres17_data:/var/lib/postgresql/data`; declare `postgres17_data` and keep `postgres_data` declared so it is never dropped. Rehearse locally: dump prod, `make dev-up` on PG17, restore, run `manage.py migrate --check` and click through the site and admin.
  1. On the droplet, check free disk space (needs about 3x the dump size). Then `cd ~/my_django_portfolio; C="docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml"`.
  2. Downtime starts: `$C stop web worker beat caddy`.
  3. Dump: `$C exec -T db pg_dump -U "$DOCKER_DB_USER" -d "$DOCKER_DB_NAME" -Fc > ~/pg13-$(date +%F).dump`. Copy it off the host (`scp`), and tar the media volume while you are at it (see finding 2).
  4. `$C stop db`. `git fetch && git checkout <PR branch>` (or apply the compose edit by hand), then `$C up -d db`. PG17 initialises the empty `postgres17_data` with POSTGRES_DB/USER/PASSWORD from .env, using scram-sha-256 auth (works with psycopg2 2.9.10).
  5. Restore: `$C exec -T db pg_restore -U "$DOCKER_DB_USER" -d "$DOCKER_DB_NAME" --no-owner --exit-on-error < ~/pg13-*.dump`, then `$C exec db vacuumdb -U "$DOCKER_DB_USER" -d "$DOCKER_DB_NAME" --analyze-in-stages`.
  6. Verify: compare `SELECT count(*)` for main_project, main_pageview, auth_user and django_migrations against the old DB (compare against the dump with `pg_restore -l`, or keep the counts from before step 2). Run `$C run --rm web python manage.py migrate --check`.
  7. `$C up -d` and smoke test: home page, project detail, admin login, manual heatmap refresh. Downtime ends. For a portfolio-sized DB (<100 MB) expect about 5-10 min.
  8. Merge the PR to main only now. The deploy workflow (`down`/`up`, docker-build-push.yml:107-109) then finds the volume already populated. **If the PR is merged before the manual cutover**, the deploy starts PG17 on an empty volume, `web` runs `migrate` (docker-compose.prod.yml:44) and the site comes up empty. A later restore then collides with the existing tables (fix: `pg_restore --clean --if-exists`).
  - Rollback: `$C down`, revert the compose commit (image 13 + `postgres_data`), `$C up -d`. The old volume is untouched. Only writes made after cutover are lost (page-view counters, task logs). Keep `postgres_data` for >= 2 weeks, then `docker volume rm my_django_portfolio_postgres_data`.
  - Alternative: `pg_upgrade` (e.g. `tianon/postgres-upgrade:13-to-17`). It is faster on large DBs but adds more moving parts, so it is not worth it at this size.
- Risk: data loss if the dump is skipped or corrupt (mitigated by the untouched old volume plus an off-host dump). Merge order (step 8) is the main trap.

## 2. No backups of Postgres or the media volume
- Severity: high | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:185-188
- Problem: `postgres_data` and `media_volume` (admin-uploaded thumbnails, markdown) are local named volumes on one droplet. Nothing in the repo dumps or copies them (grep for pg_dump/backup/rclone finds only audit docs). If the droplet or disk is lost, or a bad migration runs, that data is unrecoverable.
- Proposal: add a host cron (no new service): nightly `docker compose ... exec -T db pg_dump -Fc ... > /var/backups/portfolio/db-$(date +%F).dump` plus `docker run --rm -v my_django_portfolio_media_volume:/m:ro -v /var/backups/portfolio:/b alpine tar czf /b/media-$(date +%F).tgz -C /m .`, `find ... -mtime +14 -delete`. Copy off-host (DO Spaces via rclone, or enable DO droplet backups). Document a restore drill in README.
- Risk: none; adds disk usage (check against finding 6 thresholds).

## 3. Deploy has no rollback path and full downtime on every release
- Severity: high | Category: ops | Effort: M
- File: .github/workflows/docker-build-push.yml:77-80, :107-112; infra/docker-compose.prod.yml:37,80,120
- Problem: the image is pushed only as `:latest`. The deploy runs `down --remove-orphans`, then `up -d --force-recreate`, which also restarts db, redis and caddy, so every deploy causes downtime. It then runs `docker image prune -af`, which deletes the previous image locally. A bad release cannot be rolled back except by reverting on main and waiting for a full rebuild. `migrate` runs on web start (compose:44) with no backup beforehand. `up -d` returns success even if web dies on migrate, so CI shows green on a broken site.
- Proposal: tag and push `:${{ github.sha }}` alongside `:latest`; compose `image: ghcr.io/stokuj/my-django-portfolio:${IMAGE_TAG:-latest}`; deploy with `IMAGE_TAG=${{ github.sha }} ... up -d --wait` (no `down`, no `--force-recreate`), so only changed containers restart. Run a `pg_dump` (finding 2) before `up`. Prune with `--filter until=168h` to keep the last week's images. Rollback: `IMAGE_TAG=<prev sha> docker compose ... up -d` (if the bad release ran a migration, migrate back first).
- Risk: low; first run must confirm GHCR push of two tags.

## 4. web and caddy have no restart policy
- Severity: high | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:33, :153
- Problem: db/redis/worker/beat use `restart: always`; `web` and `caddy` have none. After a droplet reboot, a Docker daemon restart or a gunicorn crash, the site stays down while the Celery services keep running.
- Proposal: add `restart: always` to both.
- Risk: none.

## 5. No container healthchecks; startup ordering by sleep
- Severity: medium | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:42, :65-67, :87, :104-107; django/main/tasks.py:24-26
- Problem: no `healthcheck:` anywhere. `depends_on` is plain, so it only orders startup. web polls with psql (`wait-for-db.sh`), and worker uses `sleep ${WORKER_START_DELAY_SECONDS:-45}`. `healthcheck_task` is defined but never called. Docker and the deploy job cannot tell a running container from a healthy one.
- Proposal: `db` healthcheck `pg_isready -U $$POSTGRES_USER`. App services get `depends_on: db: {condition: service_healthy}`, and the sleep and wait-for-db.sh go away. `web` healthcheck `python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/')"`; worker `celery -A config inspect ping -d celery@$$HOSTNAME`. This pairs with `up --wait` from finding 3. Delete `healthcheck_task` if it is not used for the worker check.
- Risk: low; tune `start_period` for migrate+collectstatic.

## 6. Disk monitoring runs once a day and alerts nobody
- Severity: medium | Category: ops | Effort: S
- File: django/config/settings.py:224-226; django/main/tasks.py:20-21, :202-247
- Problem: `check_disk_usage_task` runs only at 06:00 UTC. The result goes only to the worker log and a TaskExecutionStatus row that is visible to admins on the about page. No ADMINS/EMAIL settings exist, so `logger.critical` reaches nobody. A disk filling up during the day (logs, images, backups) is noticed only after an outage.
- Proposal: use DigitalOcean Monitoring's native alert policy (disk > 85%, email). It is free, needs no code and also covers a stalled worker. Keep the task as the dashboard signal, or move it to `crontab(minute=0)`.
- Risk: none.

## 7. Gunicorn runs one sync worker with no access log
- Severity: medium | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:46; infra/Caddyfile:16-30
- Problem: `gunicorn config.wsgi:application --bind 0.0.0.0:8000` uses the default of 1 sync worker. A single slow request blocks the whole site. There is no access log (gunicorn default off, Caddyfile has no `log`), so traffic and errors cannot be diagnosed after the fact.
- Proposal: `gunicorn ... --workers 3 --timeout 30 --access-logfile -` (stdout is already rotated by the json-file driver, compose:70-74).
- Risk: more RAM (~3x Django process); check droplet size.

## 8. Concurrent deploys are not serialized
- Severity: low | Category: ci | Effort: S
- File: .github/workflows/docker-build-push.yml:3-6, :82-86
- Problem: there is no `concurrency:` group. Two quick merges to main run two SSH deploys whose `down`/`up`/`prune` steps can interleave, and the older run can finish last.
- Proposal: `concurrency: { group: deploy-prod, cancel-in-progress: false }` on the workflow or the deploy job.
- Risk: none.

## 9. Dead self-rescheduling heatmap code (hazardous if re-enabled)
- Severity: low | Category: simplification | Effort: S
- File: django/main/tasks.py:250-257; django/main/views.py:189-197
- Problem: `_maybe_schedule_next_refresh` runs only with `schedule_next=True`, and no caller passes that (beat: settings.py:218, views.py:452 pass False). `_schedule_next_heatmap_refresh` in views.py is never called. If it were re-enabled, chaining `countdown=3600` on top of the hourly beat would double the refreshes. A countdown equal to the Redis transport's default `visibility_timeout` (3600 s) also causes duplicate redelivery.
- Proposal: delete both helpers and the `schedule_next` kwarg; beat already owns the schedule.
- Risk: none (update tests/beat kwargs).

## 10. TaskExecutionLog grows unbounded
- Severity: low | Category: ops | Effort: S
- File: django/main/tasks.py:260-271; django/main/models.py:146; django/main/views.py:320
- Problem: every run appends a row: 24 heatmap + 12 markdown + 1 disk = about 37/day, about 13.5k/year, plus manual runs. Nothing prunes the table. The about page sorts by `last_run_at`, which has no index. This is harmless today but grows forever.
- Proposal: in `_log_task_execution`, after the create, add `TaskExecutionLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=90)).delete()`.
- Risk: none.

## 11. No Celery time limit / no lock on overlapping runs
- Severity: low | Category: ops | Effort: S
- File: django/config/settings.py:208-214; django/main/tasks.py:31, :114; django/main/views.py:429, :452
- Problem: there is no `CELERY_TASK_TIME_LIMIT`. HTTP calls have timeouts (github_client.py:55,121; markdown_sync.py:99), but nothing else guards a hung worker. Admin endpoints can enqueue a run while beat's run is in progress. The tasks are idempotent overwrites (last writer wins), so the overlap is harmless, apart from a possible IntegrityError from `get_or_create` on the unique `task_name` when two runs start together the very first time. There is no retry policy: the next beat tick acts as the retry, which is acceptable here.
- Proposal: `CELERY_TASK_TIME_LIMIT = 600` as a safety net. No lock needed.
- Risk: none.

## 12. Beat entry name says hourly, schedule is every 2 h
- Severity: low | Category: docs | Effort: S
- File: django/config/settings.py:220-222
- Problem: `"sync-project-markdowns-hourly"` uses `crontab(hour="*/2", minute=0)`.
- Proposal: rename the key to `...-every-2h`. A stale `celerybeat-schedule.db` entry is harmless.
- Risk: none.
