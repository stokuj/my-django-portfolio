# F-002 (reproduce lens): make verify / CI never runs the 96 Django app tests

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Reasoning
- `Makefile:38` runs `uv run python django/manage.py test` with no label from the repo root. Django's runner discovers from the CWD (`.`).
- `django/__init__.py` does not exist, so unittest discovery does not descend into `django/` and finds only `tests/` (it has `tests/__init__.py`).
- `.github/workflows/django.yml:46` runs `make verify` from the checkout root. The CI `.env` (lines 41-43) sets no `DB_ENGINE`, so `settings.py:111` falls back to sqlite3 and the run succeeds with only the operational tests.
- Reproduced at HEAD, with sqlite3 forced via env vars:
  - `manage.py test` from root, run as Makefile:38 runs it: `Ran 26 tests`, and every test comes from `tests.test_operational_*`
  - `manage.py test main`: `Ran 96 tests`, OK
  - `manage.py test main tests`: `Ran 122 tests`, OK
  - `cd django && manage.py test`: `Ran 96 tests` (so the command does work, but only when run from `django/`)
- `CLAUDE.md:11` and `CLAUDE.md:23` describe the root-level command as running "Django tests"/"Django app tests", which is misleading.

## Better proposal
The proposal holds. Change `Makefile:38` to `... django/manage.py test main tests` (122 tests pass today). In CLAUDE.md:23, add the `main` label, or note that the command must be run from `django/`.
