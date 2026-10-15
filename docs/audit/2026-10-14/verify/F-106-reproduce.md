# F-106 — Routine patch/minor bumps available (reproduce)

**Verdict:** CONFIRMED (with corrections)
**Confidence:** high
**Adjusted severity:** low

## Reasoning

Pinned versions at HEAD match the finding:
- `pyproject.toml:11` django-environ==0.12.0, `:12` gunicorn==23.0.0, `:13` markdown==3.8.2, `:17` pymdown-extensions==10.16.1, `:19` requests==2.33.0, `:26` ruff==0.11.10.

Latest on PyPI (checked 2026-10-15): django-environ 0.14.0, gunicorn 26.2.0, markdown 3.11.1, pymdown-extensions **12.3** (finding says 12.2), requests 2.34.2, ruff 0.17.0. npm latest: tailwindcss 4.3.3, @tailwindcss/cli 4.3.3, daisyui 5.7.50.

Corrections:
- Title is wrong: gunicorn 23 -> 26 and pymdown-extensions 10 -> 12 are **major** bumps, not "routine patch/minor". Treat these two separately.
- npm side: `package.json:8-10` use caret ranges (`^4.1.4`, `^5.0.28`), and CI installs with `npm ci` (`.github/workflows/django.yml:37`, `docker-build-push.yml:42`), so the real versions come from package-lock.json, which this audit is not allowed to read. "npm is behind" is therefore unverified; the manifest allows the latest versions already.
- The arithmatex risk is real: `django/main/views.py:364-368` uses `pymdownx.arithmatex` with `generic: True`, and `django/main/tests/test_views.py:484` asserts `class="arithmatex"` in the output, so tests would catch a markup change.
- ruff bump could surface new lint findings in `make verify` (`Makefile:39`); rule set is only E/F/I (`pyproject.toml:43`), so the risk is small.

## Better proposal

Bump the minor bumps together in one PR (django-environ, markdown, requests, ruff; `npm update` for the lockfile). Do gunicorn 26 and pymdown-extensions 12 in a separate PR, after reading their changelogs, with `make verify` passing (the arithmatex test covers pymdown).
