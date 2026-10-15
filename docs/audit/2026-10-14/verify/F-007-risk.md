# F-007 (risk lens): PostgreSQL 13 is EOL; upgrade was reverted and blocks Django 5.2

**Verdict:** CONFIRMED (not refuted). The proposal needs hardening.
**Confidence:** high
**Adjusted severity:** high (unchanged). On its own, an EOL Postgres is medium: the DB listens only on `127.0.0.1:15432` (`infra/docker-compose.prod.yml:10-11`) and on the internal network. It stays high because it blocks Django 5.2 (F-011), and Django 5.1 (`pyproject.toml:10`, `django==5.1.15`) is also EOL and serves the public web.

## Verified facts
- `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` both use `postgres:13`. The data lives in `postgres_data` (prod.yml:13) and `postgres_dev_data` (dev.yml:12).
- Commit b8da60e changes one line in the prod compose ("migration deferred").
- Spec 4a (`docs/superpowers/specs/2026-05-14-codebase-audit-design.md:114-158`) is written as an action. Nothing marks it as not done.
- Every merge to main runs a deploy on the host (`.github/workflows/docker-build-push.yml:96-109`): `git pull`, then `down --remove-orphans`, then `up -d --force-recreate`. `down` runs without `-v`, so volumes are kept.
- web runs `migrate` on every start (prod.yml:44). wait-for-db loops forever while the DB is down (`django/entrypoints/wait-for-db.sh:15-18`).

## Risks in the proposed fix (not covered by the finding)
1. **Keeping the volume name.** Suppose only the tag changes (17) and `postgres_data` stays. PG17 refuses the PG13 data dir, and `restart: always` keeps restarting it. web hangs in wait-for-db, so the site is down. No data is lost. This is what the revert in b8da60e avoided.
2. **Renaming the volume and merging before the cutover.** Compose creates an empty volume and the entrypoint inits a fresh DB. `migrate` builds an empty schema and the site comes up with no data. The finding names this risk, but "merge only after cutover" relies on discipline and nothing enforces it.
3. **Manual cutover before the merge.** The deploy script runs `git pull` on the host (workflow:98-101). If someone edited the compose file on the host for the cutover, the next deploy does one of two things. The pull aborts on local changes (`script_stop: true`), so deploys stop working. Or, with an override file, the next deploy starts pg13 again on the old volume. That is a silent rollback, and writes made after the cutover now live only in the PG17 volume.
4. **Dev volume.** If dev moves to 17 and keeps `postgres_dev_data`, every developer's `make dev-up` breaks (same case as risk 1). The dev volume also needs a new name, or the docs need a "reset the dev DB" step.
5. **Minor.** The PG14+ images default to scram-sha-256. The client is psycopg2-binary 2.9.10 (`pyproject.toml:16`), whose bundled libpq supports scram, so this is fine. `pg_restore --exit-on-error` can trip on `public` schema objects that already exist. Do one dry run on a copy of the dump first.

## Better proposal
- Give the new volume a different name and make it external, so a missing volume stops the deploy instead of starting an empty DB:
  ```yaml
  db:
    image: postgres:17
    volumes: [postgres17_data:/var/lib/postgresql/data]
  volumes:
    postgres17_data:
      external: true
      name: my_django_portfolio_postgres17_data
  ```
  `up` then fails if the volume is missing. Risk 2 is closed by the config, not by discipline.
- Order of work on the host, with no compose edits on the host:
  1. `pg_dump -Fc` from the running pg13 and copy it off the host.
  2. `docker volume create my_django_portfolio_postgres17_data`.
  3. Start a throwaway `postgres:17` container on that volume, using the same `POSTGRES_*` env. Run `pg_restore --no-owner`, then `vacuumdb --analyze-in-stages`, then compare row counts.
  4. Stop web, worker and beat. Take a final dump and restore it again, or freeze writes before step 1. Writes are low (page views and task logs).
  5. Merge the compose change. The normal deploy then picks up the filled volume.
- Leave `postgres_data` alone so rollback is possible: revert the compose change and redeploy.
- Dev: rename the volume in the same change. A non-external name is fine there; an empty DB in dev is acceptable.

Effort M is still correct.
