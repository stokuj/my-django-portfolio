# F-020 (worth lens): Ruff does not lint the Django app (31 violations)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (was medium)

## Reasoning

- `Makefile:39` runs `uv run ruff check infra/scripts tests`; `django/` is never linted. CI runs `make verify`, so the app code gets no lint gate.
- `pyproject.toml:38-43` has `[tool.ruff]` with `select = ["E","F","I"]` and no excludes.
- Reproduced at HEAD: `ruff check django --exclude django/main/migrations` reports exactly 31 errors (15 I001, 11 E501, 3 F401, 2 F841). `ruff check . --extend-exclude django/main/migrations` gives the same 31, so nothing outside `django/` breaks. 18 of them are auto-fixable.
- F401/F841 locations match the finding: `django/main/tests/test_tasks.py:2`, `test_models.py:290`, `test_models.py:301`, `test_tasks.py:98`, `test_tasks.py:200`.
- About the deliberate decision: `docs/superpowers/plans/2026-05-09-issue-53-followup-fixes.md` (Task 1) narrowed the check from `ruff check .` to `scripts tests` on purpose, "without forcing a repository-wide lint cleanup unrelated to Issue 53". That plan postponed the cleanup to keep the issue in scope. It did not decide against linting `django/`. So the proposal finishes postponed work and does not contradict that plan. The finding's wording ("although the spec required `ruff check .`") leaves out this context.
- Why the severity drops: all violations are style issues or dead code in tests. None is a runtime bug or a security gap. The two F841 `second` variables in test_tasks.py may hide a missing assertion, which is worth a quick look when fixing them.

## Better proposal

Same direction, smallest diff:
1. Add `extend-exclude = ["django/main/migrations"]` under `[tool.ruff]` in `pyproject.toml`. Migrations are generated code, with 18 extra violations, mostly E501.
2. Change `Makefile:39` to `uv run ruff check .`, and update the matching line in CLAUDE.md "Linting".
3. Run `uv run ruff check . --fix` (18 fixes). Fix the 11 E501 and 2 F841 by hand. Before deleting `second` in test_tasks.py:98/200, check whether it should be asserted.
Put the mechanical `--fix` changes in their own commit so review stays easy.
