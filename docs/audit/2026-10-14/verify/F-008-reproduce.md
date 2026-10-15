# F-008 - web and caddy have no restart policy in prod (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Reasoning
- `infra/docker-compose.prod.yml`: `restart: always` is set only on db (:4), redis (:24), worker (:82) and beat (:122).
- `web` (:33-74) and `caddy` (:153-177) have no `restart:` key. Docker's default policy is `no`.
- No other restart mechanism is in the repo: no compose override, no systemd unit or cron (`git ls-files` shows only the dev/prod compose files and `infra/scripts/compose_status.py`; grep for `restart` finds nothing in `infra/scripts` or `.github/workflows`).
- Deploy (`.github/workflows/docker-build-push.yml:107-109`) runs `pull` / `down` / `up -d --force-recreate` once. It does not keep containers running after that.
- Result: after a host reboot or dockerd restart, db/redis/worker/beat come back but web and caddy stay stopped, so the public site is down until someone redeploys by hand. The trigger is reachable.
- Small correction to the finding: the "gunicorn crash" case is weaker than stated. The gunicorn master respawns workers itself. Only a master or container exit (for example a failed `migrate` at :44) leaves web down. The reboot case alone justifies high.

## Better proposal
Add `restart: always` to `web` and `caddy` in `infra/docker-compose.prod.yml`, matching the other prod services. Optionally add one invariant test in `tests/test_operational_files.py` asserting that every prod service declares a restart policy, so this cannot regress. Effort: S.
