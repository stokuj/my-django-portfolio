# F-013 (worth): CI workflow uses deprecated actions, unlocked uv sync and stale steps

**Verdict:** CONFIRMED (worth doing, cheap), but the severity is overstated.
**Confidence:** high
**Adjusted severity:** low (CI hygiene; nothing is broken today)

## Reasoning
- `.github/workflows/django.yml:18` uses `actions/checkout@v3` and `:26` uses `actions/setup-python@v4`, both Node 16 actions. The runner forces them onto a newer Node and prints deprecation warnings. CI still runs, which is why this is low, not medium.
- `:12-15` sets up a matrix with one entry (`3.13`) and `max-parallel: 4`, which does nothing. `pyproject.toml:5` already pins `>=3.13,<3.14`.
- `:5,7` triggers on `master`, which does not exist (`git branch -r` shows only `origin/main` and `origin/audit/...`). This is harmless dead config. `docker-build-push.yml:5,86,100-101` has the same `master` leftovers, and the proposal does not mention them.
- `:32-34`: `pip install uv` is unpinned, and `uv sync --extra dev` runs without `--locked`. `uv lock --check` passes at HEAD, so nothing is drifting today. Adding `--locked` is a one-word guard against a stale lock.
- `:39-43`: the `.env` step is redundant. Every `Makefile` verify line that loads Django settings passes `SECRET_KEY`, `DJANGO_DEBUG` and `ALLOWED_HOSTS` inline (`Makefile:36-38`). `compileall` (`:35`) and `ruff` (`:39`) do not load settings. `django-environ`'s `read_env` (`django/config/settings.py:29`) only warns when the file is missing and does not override existing env vars.
- The git log (`5bd5618`, `ba5d0e0`, `1bd7024`) shows no deliberate decision to keep any of these steps.

## Corrections to the proposal
- "checkout@v4+ / setup-python@v5+" is not enough. v4 and v5 run on Node 20, which is now deprecated too. Use the Node 24 majors: `actions/checkout@v5`, `actions/setup-python@v6`, and also `actions/setup-node@v5` (the finding misses `:20`, which uses `@v4`, a Node 20 action).
- `--locked` only protects CI. Production installs with `uv pip install --system .` (`infra/Dockerfile:26-27`), which ignores `uv.lock` entirely, so CI and the image can still resolve different transitive dependencies. That gap is real but belongs in a separate finding (Docker: `uv sync --locked --no-dev`). Do not claim that `--locked` in CI closes it.
- Docs drift: `CLAUDE.md` calls the workflow `django-ci.yml`, but the file is `.github/workflows/django.yml`.

## Better proposal (smallest diff)
In `django.yml`:
1. Delete `strategy:` (`:12-15`) and use `python-version: "3.13"`.
2. `branches: [ main ]` (`:5,7`).
3. Bump to `actions/checkout@v5`, `actions/setup-node@v5` and `actions/setup-python@v6`. Optionally replace the pip+uv lines with `astral-sh/setup-uv` pinned to a version.
4. Change to `uv sync --locked --extra dev`.
5. Delete the `.env` step (`:39-43`).

Effort: S.
