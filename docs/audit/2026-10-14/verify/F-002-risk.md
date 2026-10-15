# F-002 (risk lens): make verify / CI never runs the 96 Django app tests

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Reasoning
- `Makefile:38` runs `django/manage.py test` with no label from the repo root. `django/` has no `__init__.py`, so discovery from `.` finds only `tests/` (it has `tests/__init__.py`).
- Reproduced at HEAD (sqlite override `DB_ENGINE=django.db.backends.sqlite3`): plain `manage.py test` gives `Ran 26 tests` with no test DB created. `manage.py test main tests` gives `Ran 122 tests ... OK`.
- `.github/workflows/django.yml:45-46` runs `make verify`. The CI `.env` (`django.yml:39-43`) sets no `DB_ENGINE`, so CI falls back to sqlite (`django/config/settings.py:111`). The CI gate has never exercised `django/main/tests/`.
- `CLAUDE.md:11` and `:23` describe this command as running the Django app tests. That is wrong.

## Risk of applying the fix
- **CI breakage:** low. All 122 tests pass today on sqlite, so CI should go green straight away. The only exposure is a later regression that was hidden before, and catching it is the point of the fix.
- **Local `make verify`:** this is a real behaviour change. The local `.env:22` sets `DB_ENGINE=postgresql`. Today the test step creates no DB. After the fix it creates a Postgres test DB, so a local verify fails unless Postgres is reachable and the user may create databases. CI is not affected.
- **Prod/migrations/security:** none. The change is test-only. No migrations, no runtime code.
- **Parity caveat:** CI tests run on sqlite while prod runs Postgres. This was already true and the fix does not make it worse.

## Better proposal
Change `Makefile:38` to:
`SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 DB_ENGINE=django.db.backends.sqlite3 uv run python django/manage.py test main tests`
- The explicit `DB_ENGINE` keeps local verify DB-free and matches CI. django-environ does not override variables already set in the environment, which the run above confirmed. Drop it if you want local verify to run against Postgres.
- Drop the `tests` label if tests/ is removed (F-049/F-053).
- Update `CLAUDE.md:23` to the same command.
Effort: S.
