# F-053 (reproduce): String-grep change-detector tests on Makefile/compose/workflow

**Verdict:** CONFIRMED (problem). The proposal is partly wrong.
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `tests/test_operational_files.py:8-95` has exactly 19 tests. All of them read files as text and check that a file exists, that a substring is present, or an exact count: `count("context: ..") == 3` (:51), `count("dockerfile: infra/Dockerfile") == 3` (:52), `count("- ../.env") == 3` (:56), `count("    logging:") == 6` (:72). The six `logging:` blocks are repeated at `infra/docker-compose.prod.yml:16,27,70,110,147,174`, so moving them into a YAML anchor would break :72 even though behaviour stays the same. The claim reproduces.
- The tests run in CI. `make verify` (`Makefile:38`) runs `django/manage.py test` from the repo root, and Django's discovery picks up `tests.test_operational_files.*`. I ran it and saw all 19 tests pass.
- They do not validate behaviour. For example, `"docker ps" in Makefile` (:64) and `"-p my_django_portfolio"` (:68) are substrings of other strings, and :68 is already covered by :42.

## Why severity drops to low
These tests do not cause a bug or a security gap. They cost a little maintenance on refactors. Several of them do pin real regression decisions: #55 `down --remove-orphans` (:79-81), and #57 prune after up (:83-95), see commits 1b44bc8 and d1d6a65.

## Problems with the proposal
1. "Delete the tests/ package" is wrong. `tests/test_operational_helpers.py` holds 7 real behaviour tests of `infra/scripts/ensure_env.py` and `infra/scripts/compose_status.py` (temp dirs and return values). Deleting the package would remove the only coverage of those scripts.
2. `Makefile:39` runs `ruff check infra/scripts tests`, so it would need updating if `tests/` were removed.
3. `docker compose -f infra/docker-compose.prod.yml config -q` in CI needs a `.env`, because the services declare `env_file: ../.env` and compose fails on a missing env_file. CI would have to create one first, for example `cp .env.example .env`.

## Better proposal
Delete only `tests/test_operational_files.py`, or keep just the #55/#57 ordering checks (:79-95) as one small test. Keep `tests/` and `test_operational_helpers.py`. If structural validation is wanted, add `cp .env.example .env && docker compose --env-file .env -f infra/docker-compose.prod.yml config -q` to the CI job. Effort: S.
