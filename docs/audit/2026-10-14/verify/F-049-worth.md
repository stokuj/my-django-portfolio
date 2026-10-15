# F-049 (worth lens): Python helpers re-implement docker ps --format and copy-if-missing

**Verdict:** CONFIRMED (worth doing, with a fuller diff than proposed)
**Confidence:** high
**Adjusted severity:** low (works correctly today; pure simplification, no bug)

## Reasoning
- `infra/scripts/compose_status.py:9-69` parses `docker ps --format '{{json .}}'` and re-renders a padded table; `Makefile:28-31` (prod-status) already gets the same columns from `docker ps --format "table ..."`.
- `infra/scripts/ensure_env.py:6-17,20-42` is copy-if-missing with argparse; the Makefile only ever calls it with `dev` (`Makefile:7`), so the `prod`/`create_if_missing=False` branch is reachable only from `tests/test_operational_helpers.py:35-43`.
- No contradiction with a deliberate decision: `docs/superpowers/specs/2026-05-09-issue-55-prod-workflow-fix-design.md:14,20,30` left dev targets unchanged as a scope limit, not on merit; its rationale (`:65`) argues shell-only targets are "self-documenting", and `:53` already accepts a bare header for an empty result. Same direction as this finding.
- Shell replacements are behavior-equivalent: missing `.env.example` makes `cp` fail and stops make, as `ensure_env.py:10-11` does.

## Gap in the proposal
Deleting the scripts as proposed breaks `make verify`/tests:
- `tests/test_operational_files.py:34-37` (`test_makefile_uses_helper_scripts`) asserts the Makefile contains `python infra/scripts/ensure_env.py` and `python infra/scripts/compose_status.py`. Must be deleted or inverted.
- `CLAUDE.md:34` documents `ruff check infra/scripts tests`; update alongside `Makefile:39`.

## Better proposal
- `Makefile:7` -> `@test -f .env || { cp .env.example .env && echo "Created .env from .env.example."; }`
- `Makefile:18-19` -> copy of prod-status (`Makefile:29-31`) with `label=com.docker.compose.project=my-django-portfolio-dev`.
- Delete `infra/scripts/` and `tests/test_operational_helpers.py`; drop `test_makefile_uses_helper_scripts` (`tests/test_operational_files.py:34-37`); `ruff check tests` in `Makefile:39` and `CLAUDE.md:34`.
- Effort S. Net about -240 lines.
