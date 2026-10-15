# F-019 - CLAUDE.md describes test commands and CI pipeline that do not exist

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (docs; misleads agents/contributors into false-green runs)

## Reasoning (reproduced at HEAD)
- CLAUDE.md:93 names `django-ci.yml`; `.github/workflows/` contains only `django.yml` and `docker-build-push.yml`. `django.yml:3-7` triggers on push AND pull_request to `main, master`, not "PRs to main". It runs `make verify`.
- CLAUDE.md:29 `uv run python -m pytest tests/` -> `ModuleNotFoundError: No module named 'pytest'`. pyproject `dev` extra has only `ruff==0.11.10`; `tests/test_operational_*.py:1` use `unittest`.
- CLAUDE.md:11/:23 and Makefile:38: label-less `django/manage.py test` run from repo root ran exactly `Ran 26 tests ... OK` (only `tests/`; `django/` has no `__init__.py`, so `django/main/tests/` is never discovered). `manage.py test main` does collect the app tests (failed here only on DB connection, proving it reaches them).
- docs/implementation.md:106 still says "The new development workflow runs ... from earlier versions are preserved in the README.md".

## Better proposal
Same as finding: rename to `django.yml`, describe push+PR on main/master; replace pytest line with `uv run python -m unittest discover -s tests -t .` (verified: 26 tests OK); use `manage.py test main` for app tests (needs DB). Fix Makefile:38 under F-002 first, then the CLAUDE.md:11 wording. Drop the transitional sentence.
