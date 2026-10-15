# F-020 — Ruff does not lint the Django app (31 violations)

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning

- `Makefile:39` — `verify` runs `uv run ruff check infra/scripts tests`; `django/` is never linted. CI (`django-ci.yml` -> `make verify`) inherits the gap.
- `pyproject.toml:38-43` — `[tool.ruff]` has `line-length = 100`, `select = ["E","F","I"]`, no `exclude`/`extend-exclude`.
- Reproduced at HEAD: `uv run ruff check django --exclude django/main/migrations --statistics` -> 31 errors: 15 I001, 11 E501, 3 F401, 2 F841. Exactly as claimed.
- F401: `django/main/tests/test_tasks.py:2` (`shutil`), `django/main/tests/test_models.py:290`, `:301` (`Project`). F841: `test_tasks.py:98`, `:200` (`second`). All match.
- Without the migrations exclude, `ruff check django` reports 49 errors, so the exclude is needed.

## Nuance (does not refute)

The "spec required `ruff check .`" framing is incomplete. The narrowing was deliberate: `docs/superpowers/plans/2026-05-09-issue-53-followup-fixes.md:44-67` replaced `ruff check .` with a scoped check because of existing repo-wide violations. So this is accepted tech debt, not a mistake, but the gap is real: undefined names (F821) and similar errors in app code are not caught, and `compileall` does not catch them either.

Note: the F401/F841 hits are all in tests. None of the current violations is a runtime bug in app code, so the value is preventing regressions, not fixing a live defect.

## Better proposal

Same as proposed, keeping the existing scope explicit:
1. Add `extend-exclude = ["django/main/migrations"]` to `[tool.ruff]`.
2. Change `Makefile:39` to `uv run ruff check .`.
3. `uv run ruff check . --fix` (fixes 18), then fix 11 E501 + 2 F841 by hand.
4. Update the stale CLAUDE.md "Linting" command (`ruff check infra/scripts tests`) to match.
Effort S.
