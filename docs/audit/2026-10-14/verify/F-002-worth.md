# F-002 (worth lens): make verify / CI never runs the 96 Django app tests

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high

## Reasoning
- `Makefile:38` runs `uv run python django/manage.py test` with no label from the repo root. `django/` has no `__init__.py`, so discovery from `.` only picks up the `tests/` package.
- Reproduced at HEAD (sqlite override): unlabeled run -> `Ran 26 tests` (19 `tests.test_operational_files` + 7 `tests.test_operational_helpers`), zero from `django/main/tests/`.
- `manage.py test main` -> 96 tests OK; `manage.py test main tests` -> 122 tests OK. All app tests pass today, so the fix does not turn CI red right now.
- CI `.github/workflows/django.yml:46` only runs `make verify`; `docker-build-push.yml` runs no tests. So the app suite has no gate anywhere.
- Contradicts `CLAUDE.md:11` ("Django tests") and `CLAUDE.md:23` (same unlabeled command presented as "Django app tests"). No docs/ or git log entry shows this was deliberate; the line dates from `441f039` (compose workflow).
- `tests/` is not run by pytest in CI either, so it currently runs only by this accident. Dropping it (e.g. `cd django && manage.py test`, 96 tests) would lose those 26; keeping both labels is right.

## Better proposal
None simpler. One-line change, `Makefile:38`:
`... uv run python django/manage.py test main tests`
plus update `CLAUDE.md:23` to the same labels (and note `CLAUDE.md:93` names `django-ci.yml`, actual file is `django.yml`). Drop the `tests` label only if F-049/F-053 removes `tests/`.
