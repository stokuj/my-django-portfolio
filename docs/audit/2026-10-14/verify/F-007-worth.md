# F-007 - PostgreSQL 13 is EOL; upgrade was reverted and blocks Django 5.2 (worth lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Reasoning
- `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` pin `image: postgres:13`. Verified.
- `git log -S"postgres:16" -- infra`: 667e27f bumped the tag, b8da60e reverted it ("migration deferred"). Only the tag changed (1 line). Verified.
- Spec `docs/superpowers/specs/2026-05-14-codebase-audit-design.md:114-128` still describes 4a as the fix, with no note that it was reverted. Its step 3 (`docker volume rm`, line 122) destroys the only copy before the restore is checked. The finding's "keep the old volume" is the right correction.
- `pyproject.toml:10` pins `django==5.1.15`. 5.1 is out of support, and 5.2 needs PG >= 14, so the PG upgrade blocks the Django security upgrade. That justifies keeping "high".
- On its own, PG13 exposure is limited: the port is bound to `127.0.0.1:15432` (`docker-compose.prod.yml:10-11`). That is a reason it is not "critical", not a reason to drop it.
- CI runs tests on SQLite only: `django/config/settings.py:111` defaults to sqlite3, and `.github/workflows/django.yml` defines no postgres service. Verified.
- Merge-before-cutover risk is real. A merge to main auto-deploys (`.github/workflows/docker-build-push.yml:5,107-109`), and web runs `migrate` on start (`docker-compose.prod.yml:44`).

## Corrections and simplifications to the proposal
1. **Rename the volume key** (for example `postgres17_data`) in the same compose change. If you don't, PG17 starts on the PG13 data dir and refuses to boot ("incompatible data directory"): you get an outage, not an empty DB. The finding's "starts an empty PG17" holds only when the volume is renamed. Renaming also makes "keep postgres_data untouched" automatic, and rollback becomes a plain revert.
2. **Host git gotcha:** if the operator edits the compose on the droplet for the cutover, the deploy's `git pull` (`docker-build-push.yml:101`) fails on the local change (`script_stop: true`). Run `git checkout -- infra/docker-compose.prod.yml` on the host before merging. Alternatively, do the cutover with `-f infra/docker-compose.prod.yml -f /tmp/pg17.override.yml` so the tracked file stays clean.
3. Dump/restore is the right tool for a small portfolio DB. Skip pg_upgrade-based images (`pgautoupgrade`, `tianon/postgres-upgrade`) as unneeded complexity. Pin `postgres:17` rather than 18: the 18 image moved PGDATA to `/var/lib/postgresql/18/docker`, which would also need a volume mount path change.
4. `vacuumdb --analyze-in-stages` and row-count comparison are optional for a DB this size. `pg_restore --exit-on-error` plus `migrate --check` plus a smoke test is enough.
5. Update spec 4a (`...audit-design.md:114-128`) to mark it reverted/open and remove the `docker volume rm` step.

## Better proposal (smallest diff)
One PR: `postgres:13` -> `postgres:17` in both compose files, rename the prod volume key to `postgres17_data` (dev: `postgres_dev17_data` or just recreate). Order of operations on the droplet:
1. `pg_dump -Fc` and copy it off-host.
2. Clean the host checkout, then merge. The auto-deploy brings up empty PG17 and migrate runs.
3. Stop web/worker/beat.
4. `dropdb`/`createdb`, then `pg_restore --no-owner --exit-on-error`.
5. Start the stack and smoke test.

Rollback: revert the PR (the old volume is untouched). Follow up with the Django 5.2 bump (F-011).
