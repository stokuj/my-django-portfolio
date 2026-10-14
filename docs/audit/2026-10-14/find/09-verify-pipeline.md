# verify-pipeline

Scope: `Makefile` `verify` target, `.github/workflows/*.yml`, test discovery, ruff scope, dev deps, CI vs Dockerfile toolchain (HEAD on `dev`).

Measured before numbers (SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1):
- `uv run python django/manage.py test` from repo root (what `make verify`/CI runs): **Ran 26 tests** - all `tests.test_operational_*`, zero `main.tests`.
- `cd django && manage.py test` (sqlite via DB_ENGINE override): **Ran 96 tests, OK**.
- `manage.py test main tests` from repo root: **Ran 122 tests, OK** (96 + 26).
- `uv run ruff check django`: **49 errors** (27 E501, 17 I001, 3 F401, 2 F841); excluding migrations: **31** (15 I001, 11 E501, 3 F401, 2 F841; 18 auto-fixable).
- `uv run ruff check infra/scripts tests`: All checks passed.
- `uv run python -m pytest`: `No module named pytest`.

## 1. Django test suite never runs in `make verify` / CI
- Severity: high | Category: tests | File: Makefile:38 | Effort: S
- Problem: `manage.py test` with no labels discovers from the CWD (repo root). `django/` has no `__init__.py`, so discovery only finds the root `tests/` package (26 operational tests). All 96 tests in `django/main/tests/` are silently skipped; CI is green regardless of app regressions.
- Proposal: `... uv run python django/manage.py test main tests` (verified: 122 tests, OK).
- Risk: locally the `.env` points at Postgres (`DB_ENGINE=postgresql`), so `make verify` will then need a running DB or `DB_ENGINE=django.db.backends.sqlite3` in the Makefile line. CI `.env` has no DB_* and falls back to sqlite (django/config/settings.py:111).

## 2. Image build/push/deploy is not gated on tests
- Severity: medium | Category: ci | File: .github/workflows/docker-build-push.yml:3-5,84 | Effort: S
- Problem: On push to main, `docker-build-push.yml` builds, pushes and deploys independently of `django.yml`; `deploy` only `needs: build-and-push`. A failing `make verify` does not stop a production deploy.
- Proposal: add a `verify` job (`make verify`) to this workflow and make `build-and-push` `needs: verify`, or trigger via `workflow_run` on Django CI success.
- Risk: deploy gets slower by the verify duration.

## 3. `workflow_dispatch` from any branch overwrites `:latest` in GHCR
- Severity: medium | Category: ops | File: .github/workflows/docker-build-push.yml:6,80 | Effort: S
- Problem: `build-and-push` has no ref guard (only `deploy` has one, line 86). Manually running the workflow on a feature branch pushes `ghcr.io/stokuj/my-django-portfolio:latest` (infra/docker-compose.prod.yml:37,80,120); the next prod `pull`/recreate deploys unreviewed code.
- Proposal: put the same `if: github.ref == 'refs/heads/main'` on `build-and-push`, or tag non-main builds with the SHA only.
- Risk: none.

## 4. Ruff does not lint the Django app
- Severity: medium | Category: ci | File: Makefile:39 | Effort: S
- Problem: lint scope is `infra/scripts tests` only. `django/` has 49 issues (31 without migrations), incl. real dead code: F401 `django/main/tests/test_models.py:290,301`, `django/main/tests/test_tasks.py:2`; F841 `django/main/tests/test_tasks.py:98,200`.
- Proposal: `uv run ruff check .` with `extend-exclude = ["django/main/migrations"]` in `[tool.ruff]` (pyproject.toml:38); run `ruff check --fix` once (18 auto-fixable), fix or `per-file-ignores` the 11 E501.
- Risk: one-off noisy diff in app files.

## 5. CI tests locked deps, image installs unlocked/upgraded deps
- Severity: medium | Category: ci | File: infra/Dockerfile:27 | Effort: S
- Problem: CI runs `uv sync --extra dev` without `--locked` (.github/workflows/django.yml:34), so a stale `uv.lock` is silently re-resolved instead of failing. The image runs `uv pip install --system .`, which ignores `uv.lock`, and `[tool.uv] pip = { upgrade = true }` (pyproject.toml:29-30) upgrades transitive deps to latest at build time. The deployed environment is not the tested one.
- Proposal: CI `uv sync --locked --extra dev`; Dockerfile `uv export --frozen --no-dev --no-hashes -o req.txt && uv pip install --system -r req.txt .` (or `uv sync --frozen --no-dev`); drop `pip.upgrade` unless intentional.
- Risk: first locked build may surface lock drift that must be resolved.

## 6. Docs describe a pipeline that does not exist
- Severity: medium | Category: docs | File: CLAUDE.md:29,93 | Effort: S
- Problem: CLAUDE.md:29 says `uv run python -m pytest tests/`, but pytest is not a dependency (pyproject.toml:24-27 dev = ruff only) -> `No module named pytest`. CLAUDE.md:93 names `django-ci.yml`; real file is `.github/workflows/django.yml`, and it triggers on push+PR to main/master, not only PRs. CLAUDE.md:8 claims verify runs Django tests (see finding 1).
- Proposal: replace pytest line with `uv run python -m unittest discover tests` (tests use `unittest`), fix the file name/trigger, update after finding 1.
- Risk: none.

## 7. Node version mismatch CI vs Dockerfile
- Severity: low | Category: ci | File: .github/workflows/django.yml:22 | Effort: S
- Problem: both workflows use `node-version: 20` (django.yml:22, docker-build-push.yml:37); the image builds CSS on `node:22-slim` (infra/Dockerfile:2). The CSS preflight in docker-build-push.yml:40-43 also duplicates the Dockerfile's css-builder stage.
- Proposal: use Node 22 in both workflows; drop the preflight step (Docker stage already fails the build on CSS errors).
- Risk: none.

## 8. Stale/redundant steps in django.yml
- Severity: low | Category: simplification | File: .github/workflows/django.yml:12-15,18,26,32-33,39-43 | Effort: S
- Problem: `actions/checkout@v3` and `actions/setup-python@v4` are outdated (other workflow uses checkout@v4); single-entry matrix with `max-parallel: 4`; `pip install uv` instead of `astral-sh/setup-uv` (no uv cache); `.env` creation step is redundant because every Makefile verify line passes `SECRET_KEY/DJANGO_DEBUG/ALLOWED_HOSTS` inline.
- Proposal: bump to checkout@v4 / setup-python@v5, drop the matrix, use `astral-sh/setup-uv` with cache, delete the `.env` step.
- Risk: none.
