# F-057 — .gitignore is the full GitHub Python template (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.gitignore` is 180 lines (`wc -l`).
- Template sections irrelevant to this repo are present: PyInstaller (`.gitignore:34`), Flask (`:69`), Scrapy (`:73-74`), Sphinx (`:76`), pdm (`:109-115`), PEP 582 (`:117`), SageMath (`:124-125`), Spyder/Rope/mkdocs/Pyre/pytype/Cython (`:139-162`).
- Project-specific entries are only a handful: `node_modules/` and `style.css` (`:1-2`), `.env` (`:128`), Celery beat files (`:121-122`), and the custom tail `:166-180` (`/.idea`, `/media/`, `/staticfiles`, `.env.dev`, `.claude/settings.local.json`, etc.).
- Extra observation: `/django/main/content` is duplicated (`:178-179`).
- No functional bug; purely readability/noise. Low severity is correct.

## Better proposal
Keep the cut, but do not hand-pick from memory: keep Python basics (`__pycache__/`, `*.py[cod]`, `.venv`, caches for ruff/pytest/mypy/coverage), `.env*`, Celery beat files, and the whole custom tail (`:166-180`), dropping the duplicate line. Verify with `git status --ignored --porcelain` before/after; the ignored set must be identical on a dev checkout.
