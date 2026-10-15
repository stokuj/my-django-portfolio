# F-107 - psycopg2-binary instead of psycopg 3

**Verdict:** CONFIRMED (low)
**Confidence:** high (on the code facts); the exact pin `3.3.6` was not checked offline
**Adjusted severity:** low

## Reasoning
- `pyproject.toml:16` pins `psycopg2-binary==2.9.10`. This is the only Postgres driver dependency.
- Nothing imports `psycopg2` directly (grep over `django/`, `tests/`, `infra/` excluding migrations). The driver is only used through `ENGINE` (`django/config/settings.py:111`, `DB_ENGINE` = `django.db.backends.postgresql` in `.github/workflows/docker-build-push.yml:20,53` and the compose files). Django uses the same `ENGINE` for psycopg 3, so the swap needs no code change.
- Django 5.1 (`pyproject.toml:10`) supports both drivers and documents psycopg2 as likely to be deprecated later. The psycopg2 docs say the `-binary` wheel is meant for dev and testing and recommend a source build in production. So the finding is accurate.
- This is hygiene, not a bug. No failure is reproducible at HEAD. 2.9.10 ships Python 3.13 wheels, which matches `requires-python` and the `python:3.13-slim` image.
- Side note: `infra/Dockerfile:17` already installs `gcc libpq-dev`. The `-binary` wheel does not need them, so they are dead weight today. They would only be used for a source build.

## Better proposal
Replace with `psycopg[binary]` pinned to a version checked against PyPI at change time (do not use `3.3.6` without checking it), then run `make verify` and a compose smoke test on Postgres. Optional: because the image already has `gcc`/`libpq-dev`, use `psycopg[c]` in the image. Otherwise drop `gcc libpq-dev` from `infra/Dockerfile:17` (keep `postgresql-client` if `wait-for-db.sh` uses it). Effort: S.
