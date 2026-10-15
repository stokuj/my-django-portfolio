# F-019 — CLAUDE.md describes test commands and CI pipeline that do not exist

**Verdict:** CONFIRMED (worth doing, with a narrower fix)
**Confidence:** high
**Adjusted severity:** low (docs/S)

## Reasoning
- `CLAUDE.md:93` names `django-ci.yml`; only `.github/workflows/django.yml` and `docker-build-push.yml` exist. `django.yml:3-7` triggers on push AND pull_request to `main, master`, not "PRs to main" only. `django.yml:46` does run `make verify`.
- `CLAUDE.md:29` `uv run python -m pytest tests/` fails: `ModuleNotFoundError: No module named 'pytest'`; `pyproject.toml:25-27` dev group has only ruff.
- `CLAUDE.md:11` / `:23` and `Makefile:38`: label-less `manage.py test` run from repo root discovers from cwd. `django/` has no `__init__.py`, so unittest discovery does not descend into `django/main/tests/`. Reproduced with the same loader: 26 tests, all from `tests/`. So "Django tests" is false today.
- `CLAUDE.md:26` (single-module `main.tests.test_views`) is correct and should stay.
- `docs/implementation.md:106` transitional "new development workflow" sentence confirmed; trivial.
- No git log or docs entry shows a deliberate choice to keep these names (CLAUDE.md last touched in 667e27f).

## Why severity lowered
The wrong file name and pytest command fail loudly or are harmless. The only misleading claim (`:11`, verify runs Django tests) is a symptom of the Makefile bug (F-002). Fix F-002 and `:11` becomes true without a doc edit.

## Better proposal
Fix F-002 first (`Makefile:38` -> `manage.py test main` plus a unittest run of `tests/`), then a 4-line CLAUDE.md edit:
- `:23` -> `... django/manage.py test main`
- `:29` -> `uv run python -m unittest discover -s tests -t .`
- `:93` -> `django.yml` runs `make verify` on push/PR to main/master
- drop the sentence at `docs/implementation.md:106` (optional).
Do not add pytest just to make the documented command work.
