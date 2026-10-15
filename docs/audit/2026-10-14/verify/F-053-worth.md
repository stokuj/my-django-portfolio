# F-053 - String-grep change-detector tests on Makefile/compose/workflow (worth lens)

**Verdict:** REFUTED (as proposed); the underlying observation is partly valid
**Confidence:** high
**Adjusted severity:** low

## Reasoning

- The diagnosis of `tests/test_operational_files.py` is accurate: 19 tests, all
  existence / substring / exact-count checks (e.g. `count("context: ..") == 3` at
  line 51, `count("    logging:") == 6` at line 72). They are change detectors.
- The proposal is wrong in scope: "Delete the file and the tests/ package" also
  deletes `tests/test_operational_helpers.py` (7 tests), which are real behavioural
  tests of `infra/scripts/ensure_env.py` and `infra/scripts/compose_status.py`
  using temp dirs (`tests/test_operational_helpers.py:1-30`). That is a coverage loss.
- "They break on harmless refactors" is overstated: the tests/ package is never
  executed in CI. `make verify` (Makefile:33-39) runs only Django tests and
  `ruff check infra/scripts tests`; `.github/workflows/django.yml:46` only runs
  `make verify`. pytest is not a dependency (pyproject.toml:25-26 has only ruff),
  so CLAUDE.md's `uv run python -m pytest tests/` command would not even work.
  All 26 tests pass with `uv run python -m unittest discover -s tests -t .`.
- The tests are a deliberate, documented decision: the issue-57 plan
  (`docs/superpowers/plans/2026-05-09-issue-57-disk-space-optimization.md:7`)
  explicitly chose "string-assertion regression tests"; commits 1b44bc8 and
  d1d6a65 added them as regression coverage for #55/#57.
- `docker compose -f infra/docker-compose.prod.yml config -q` validates syntax
  only; it does not check what these tests guard (logging on every service,
  prune-after-up order in `docker-build-push.yml`). It is not a replacement,
  just an additional check. It would work in CI since `.env` is created at
  `django.yml:39-42`.

## Better proposal

The real gap is that `tests/` never runs. Smallest useful diff:
1. Add `uv run python -m unittest discover -s tests -t .` to the `verify` target
   (Makefile:39), so the helper tests actually guard something. Fix the
   CLAUDE.md command (pytest -> unittest).
2. Optionally trim `test_operational_files.py` to the few #55/#57 invariants
   (or drop it if the owner no longer wants them). Keep `test_operational_helpers.py`.
3. Optionally add `docker compose ... config -q` to verify for syntax validation.

Effort: S.
