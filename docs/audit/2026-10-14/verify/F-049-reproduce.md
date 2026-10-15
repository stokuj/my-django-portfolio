# F-049 (reproduce): Python helpers re-implement docker ps --format and copy-if-missing

**Verdict:** CONFIRMED (with one omission in the proposal)
**Confidence:** high
**Adjusted severity:** low (simplification, no runtime defect)

## Reasoning
- `infra/scripts/compose_status.py:1-91` runs `docker ps -a --filter label=... --format '{{json .}}'` (`:40-69`), then re-renders a padded NAME/STATUS/IMAGE/PORTS table (`:9-37`). `prod-status` gets the same table from one `docker ps --format "table ..."` call (`Makefile:28-31`). Only difference: empty result prints "No matching containers found." (`:10-11`) instead of a bare header.
- `infra/scripts/ensure_env.py:1-46` is copy-if-missing with argparse and `prod` mode (`:22,31`). Only caller is `Makefile:7` with `dev`; `prod` mode is unused (`prod-up` uses the shell guard at `Makefile:22`).
- Tests: `tests/test_operational_helpers.py` (4 ensure_env + 3 table tests). Note: `make verify` (`Makefile:33-39`, CI `.github/workflows/django.yml:46`) never runs `pytest tests/`, so these tests are only ruff-linted in CI.

## Gaps in the proposal
- `tests/test_operational_files.py:34-37` (`test_makefile_uses_helper_scripts`) asserts the Makefile contains both script calls; it must be deleted too, or `pytest tests/` fails.
- `CLAUDE.md:34` and `:90` mention `infra/scripts`; update them.
- `ruff check infra/scripts tests` (`Makefile:39`) -> `ruff check tests`.
- Minor: the finding cites CI as `django-ci.yml`; the actual file is `.github/workflows/django.yml`.

## Better proposal
As proposed (dev-status = prod-status line with `label=com.docker.compose.project=my-django-portfolio-dev`; dev-up = `@test -f .env || { cp .env.example .env && echo "Created .env"; }`; delete `infra/scripts/` and `tests/test_operational_helpers.py`), plus delete `test_makefile_uses_helper_scripts` in `tests/test_operational_files.py:34-37`, fix `Makefile:39` and `CLAUDE.md:34,90`. Effort S.
