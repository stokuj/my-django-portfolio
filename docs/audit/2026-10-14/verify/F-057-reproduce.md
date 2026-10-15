# F-057 — .gitignore is the full GitHub Python template

**Verdict:** CONFIRMED (reproduce lens)
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning
- `.gitignore` is 180 lines (`wc -l`). Lines 6-165 are the stock GitHub Python template:
  PyInstaller (`.gitignore:34-38`), Flask (`:69`), Scrapy (`:73`), Sphinx (`:76`),
  pdm (`:109-115`), PEP 582 (`:117-118`), SageMath (`:124-125`), Spyder/Rope/mkdocs/Pyre/pytype/Cython (`:136-158`).
- Project-specific entries are only at `.gitignore:1-2` and `:166-180`.
- Extra detail not in the finding: `/django/main/content` is duplicated at `.gitignore:178-179`.
- No functional harm today: `git ls-files -ci --exclude-standard` returns nothing (no tracked file is shadowed by a template rule).
  Impact is pure noise, so "low / simplification" is correct.

## Caveats for the proposal
Some template lines ARE relevant and must survive a trim:
- `celerybeat-schedule`, `celerybeat.pid` (`:121-122`) — Celery beat runs in this project.
- `__pycache__/`, `*.py[cod]` (`:7-8`), `.venv` / `.env` (`:128-129`), `.pytest_cache/` (`:56`), `.coverage*` (`:48-49`), `.mypy_cache/`.
- `git status --ignored` currently shows: `.claude/settings.local.json`, `.env`, `.idea/`, `.ruff_cache/` (self-ignored via its own .gitignore), `.venv/`, `__pycache__/` dirs, `django/main/static/css/`, `node_modules/`.

## Better proposal
Trim to ~25 lines (project block + __pycache__, *.py[cod], .venv, .env, .env.dev, .pytest_cache, .coverage*, htmlcov, .mypy_cache, celerybeat-schedule/pid, dist/build/*.egg-info, IDE/OS lines), drop the duplicate `/django/main/content`.
Verify: diff `git status --ignored --porcelain` and `git ls-files -ci --exclude-standard` before/after. Effort S. Purely cosmetic; skip if no one is touching the file.
