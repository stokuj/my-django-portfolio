# F-008 (risk lens): web and caddy have no restart policy in prod

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Evidence
- `infra/docker-compose.prod.yml:4,24,82,122`: db, redis, worker, beat have `restart: always`.
- `infra/docker-compose.prod.yml:33-74` (web) and `:153-178` (caddy): no `restart:` key. Default policy is `no`.
- Deploy (`.github/workflows/docker-build-push.yml:107-109`) only runs `compose pull/down/up -d`; no systemd unit or other supervisor brings the stack back. After a host reboot or dockerd restart, db/redis/worker/beat come back, but web and caddy stay down, so the site is offline until someone runs `up -d` by hand.

## Risk of applying the fix
- Low. It is a compose-only change; no migration, no image change, no security regression.
- web runs `migrate && collectstatic && gunicorn` at start (`:43-46`). With a restart policy, a failing migration or bad env (e.g. missing `SECRET_KEY`) becomes a crash loop instead of a stopped container. Docker backs off exponentially; logs are capped by `max-size 10m / max-file 3` (`:70-73`). Postgres migrations run in transactions, so repeating them does no damage. Acceptable.
- `wait-for-db.sh` (`django/entrypoints/wait-for-db.sh:15`) already blocks until Postgres is up, so the boot-order race on reboot is handled (`depends_on` without conditions is not honoured on daemon restart, but the script covers it).
- Small overstatement in the finding: a crashed gunicorn *worker* is respawned by the gunicorn master. The restart policy only helps when the master or the whole container exits. The reboot/dockerd case is the real one.
- `always` vs `unless-stopped`: `always` also restarts containers someone stopped on purpose, after a dockerd restart. `unless-stopped` avoids that, but `always` matches the other four services. Either works.

## Better proposal
Add `restart: always` to web and caddy, matching the rest of the file. Optionally add a check in `tests/test_operational_files.py` that every service in the prod compose file has a `restart` key, so a new service cannot miss it again.
