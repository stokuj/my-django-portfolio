# F-058 (reproduce lens): compileall in verify is redundant

**Verdict:** REFUTED
**Confidence:** medium
**Adjusted severity:** low (if kept at all; not worth a change on its own)

## Reasoning
- The line exists as cited: `Makefile:35` runs `uv run python -m compileall django`.
- The claim that `check` + tests "already import every module that matters" does not hold:
  - `django/config/wsgi.py` is the production entrypoint (`infra/docker-compose.prod.yml:46`, `gunicorn config.wsgi:application`). It is referenced only as a string in `settings.py:91` (`WSGI_APPLICATION`), which `manage.py check` / `test` never import. No test imports it (grep over `django/` and `tests/` finds no import of `wsgi`/`asgi`).
  - `django/config/asgi.py` is likewise imported by nothing.
  - `Makefile:39` lints only `infra/scripts tests`, so ruff does not cover `django/` either.
  - So at HEAD, compileall is the only gate in `make verify` that would catch a syntax error in `wsgi.py`. Removing it would let a broken Gunicorn entrypoint pass CI (`.github/workflows/django.yml:46`) and fail only at deploy.
- "Writes .pyc into the tree" is not a real harm: `__pycache__/` is gitignored (`.gitignore:7`), and `manage.py check`/`test` write the same `.pyc` files anyway.
- Cost is negligible: `compileall -q django` took ~0.12 s locally.
- The finding's own "risk" field names exactly this gap, which contradicts the "redundant" claim.

## Better proposal
Keep the line. If simplification is wanted, replace it with something that also covers `django/`, e.g. extend `Makefile:39` to `uv run ruff check django infra/scripts tests` (ruff reports syntax errors), and only then drop `compileall`. That is a separate decision, not part of F-002.
