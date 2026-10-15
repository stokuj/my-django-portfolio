# F-013 (reproduce lens): CI workflow uses deprecated actions, unlocked uv sync and stale steps

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
Every factual claim matches `.github/workflows/django.yml` at HEAD:
- `actions/checkout@v3` (18) and `actions/setup-python@v4` (26) are the Node 16 major versions, which are deprecated. They still run because GitHub forces them onto Node 20, so this produces warnings, not failures.
- The matrix has one entry, `python-version: [3.13]` (14-15), with `max-parallel: 4` (13). That is dead config. `pyproject.toml:5` pins `>=3.13,<3.14`, so the matrix cannot grow anyway.
- The workflow triggers on `master` (5, 7). No `master` branch exists locally or on origin (`git ls-remote` returns only `main`).
- `pip install uv` is unpinned (33), and `uv sync --extra dev` runs without `--locked` (34) even though `uv.lock` is committed. When the lockfile drifts from `pyproject.toml`, uv re-resolves it silently in CI and CI does not fail. `pip install --upgrade pip` (32) is also unneeded.
- The `.env` step (39-43) is redundant. `Makefile:36-38` sets `SECRET_KEY`, `DJANGO_DEBUG` and `ALLOWED_HOSTS` inline for every `manage.py` call. `npm run build:css:prod`, `compileall` and `ruff` (34-35, 39) do not need them. `settings.py:29` `read_env` does not override variables that are already set, and a missing file does not cause an error. No Django test references `.env`.

## Why the severity is lower
None of these items makes a CI run wrong today. The only one with real impact is the missing `--locked`, which can let an out-of-date `uv.lock` reach `main`. The Docker build may install from that lock, so the risk is low. The rest is hygiene.

## Better proposal
Replace lines 25-34 with `astral-sh/setup-uv` pinned to a major version (with `enable-cache: true`), then run `uv sync --locked --extra dev`. Bump checkout to v4 or later. Drop the matrix/strategy block, `master`, and the `.env` step. Effort: S.
