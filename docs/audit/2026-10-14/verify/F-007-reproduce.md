# F-007: PostgreSQL 13 is EOL; upgrade was reverted and blocks Django 5.2

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (inherits high priority only as the blocker for F-011)

## Evidence (HEAD, branch dev)
- `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` both use `image: postgres:13`.
- `git show b8da60e` changes only that one line in prod compose (`postgres:16` -> `postgres:13`), message "migration deferred". The bump came from 667e27f and touched only the tag, with no data migration.
- `pyproject.toml:10` pins `django==5.1.15`. Django 5.2 drops PG13 support, so the upgrade path really is blocked.
- CI is `.github/workflows/django.yml` (the finding names it `django-ci.yml`). It runs `make verify` (`Makefile:33-39`) with only SECRET_KEY/DEBUG/ALLOWED_HOSTS in `.env` (`django.yml:39-43`). `settings.py:111-112` therefore falls back to SQLite, so CI never exercises Postgres.
- The audit spec `docs/superpowers/specs/2026-05-14-codebase-audit-design.md:114-130` still describes 4a as the fix. The plan `docs/superpowers/plans/2026-05-14-codebase-audit.md:1255` marks "✅ 4a postgres:13 → 16 → Task 12". That checkmark is a spec-coverage mapping, not a completion status, but nothing records the revert.

## Why the severity is lower
- The DB port is bound to `127.0.0.1:15432` (`docker-compose.prod.yml:10-11`) and lives on the internal `app-network`. Nothing exposes PG to the internet, so no remote attack path reaches it directly. That makes it ops/security debt, not an exploitable gap.
- The real exposure is indirect. Django 5.1 is past its own EOL and cannot move to 5.2 LTS while PG13 stays. That risk belongs to F-011, and this finding is its prerequisite.

## Better proposal
The proposal (dump/restore onto a new volume and keep `postgres_data`) is sound and safer than spec 4a. Spec 4a runs `docker volume rm` before the restore is verified (`design.md:122`), and that step should be removed or rewritten. Additions:
- Use a new named volume (e.g. `postgres17_data`) in compose, so a premature deploy fails safe: an empty DB, while the old volume stays intact. Do not reuse the `postgres_data` name.
- Bump dev compose in the same change. Optionally add a `postgres:17` service to `django.yml` so CI tests against the prod engine.
- Update the spec/plan 4a to note the revert and the new procedure.
