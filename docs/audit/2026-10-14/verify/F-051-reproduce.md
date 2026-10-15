# F-051 — Celery 5.4.0 does not support Python 3.13 (reproduce lens)

**Verdict:** CONFIRMED in fact, OVERSTATED in impact
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `pyproject.toml:9` pins `celery[redis]==5.4.0`; `pyproject.toml:5` requires `>=3.13,<3.14`.
- `Dockerfile:10` is `FROM python:3.13-slim`; CI `.github/workflows/django.yml:15` uses 3.13.
- Installed `.venv/.../celery-5.4.0.dist-info/METADATA:23-27` lists classifiers 3.8–3.12 only. So "not officially supported on 3.13" holds.
- But it is not broken: in the local 3.13.12 venv, `celery -A config report` runs (celery 5.4.0, kombu 5.6.2, billiard 4.2.4), and importing `celery.bin.worker`, `celery.beat`, `celery.app.task` with `-W error::DeprecationWarning` succeeds. The stack has been in prod on 3.13 with no failure reported in code/tests.
- No code path in the repo depends on a 3.13-specific fix from 5.5+. Task tests could not be run here (no Postgres), so runtime of worker/beat not exercised locally.
- "Latest is 5.6.3" not verified offline.

## Better proposal
Low-priority hygiene: bump to the latest 5.5.x/5.6.x in a routine dependency update (uv lock), run `make verify` plus a manual worker/beat smoke in dev compose. Not a medium bug; title should read "Celery 5.4.0 not officially supported on Python 3.13".
