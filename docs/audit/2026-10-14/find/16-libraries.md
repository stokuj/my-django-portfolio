# Libraries

Scope: pyproject.toml, package.json, infra/Dockerfile, CI workflows, CDN scripts at HEAD (dev). Latest versions from PyPI/npm/GitHub APIs, CVEs from OSV (queried 2026-10-15). Lock files not read.

No replacement library recommended for the GitHub client (github_client.py, ~180 lines, REST+GraphQL) or task observability (TaskExecutionStatus/Log carry custom partial-success semantics); PyGithub/django-celery-results would add weight without removing much.

## 1. Django 5.1 is EOL with unpatched CVEs
- Severity: high | Category: security | File: pyproject.toml:10
- Problem: `django==5.1.15`. 5.1 reached EOL 2025-12-03; OSV lists 8 advisories fixed only in 5.2.15-5.2.17 / 6.0.x (signed-cookie salt collisions, DomainNameValidator header injection, cache-middleware leaks). Latest LTS patch is 5.2.18 (supported to 2028-04).
- Proposal: bump to `django==5.2.18`. Grep for 5.2 deprecations (`finders.find(all=)`, `ArrayAgg/StringAgg ordering=`, `OrderableAggMixin`, `create_test_db(serialize=)`) found no usage in django/; the blocker is PostgreSQL (finding 2).
- Effort: S (after finding 2) | Risk: run full app test suite (see finding 3, it does not currently run in CI).

## 2. PostgreSQL 13 is EOL and blocks Django 5.2
- Severity: high | Category: ops | File: infra/docker-compose.prod.yml:3 (also infra/docker-compose.dev.yml:3)
- Problem: `image: postgres:13`. PG13 EOL 2025-11-13. Django 5.2 release notes: "Dropped support for PostgreSQL 13 ... supports PostgreSQL 14 and higher" (Django refuses to connect below minimum version). Commit b8da60e reverted 16 -> 13 with "migration deferred". PG14 itself ends 2026-11-12.
- Proposal: dump/restore to `postgres:17` (or 16) with a pinned major, then bump Django.
- Effort: M | Risk: data migration of the prod volume; needs pg_dump backup and restore rehearsal.

## 3. `make verify` / CI never runs the Django app tests
- Severity: high | Category: ci | File: Makefile:38
- Problem: `manage.py test` is run from the repo root, so discovery starts at `.` and only finds `tests/` (verified: `-v 2` lists 26 tests, all `tests.test_operational_*`). The 96 tests in django/main/tests/ are never executed in CI (django.yml runs `make verify`). Any dependency bump in this report is currently unguarded.
- Proposal: `uv run python django/manage.py test main` (labels resolve via sys.path), keep `tests/` via pytest as CLAUDE.md documents.
- Effort: S | Risk: hidden failures may surface once the suite actually runs.

## 4. Docker image ignores uv.lock and resolves deps at build time
- Severity: medium | Category: library | File: infra/Dockerfile:27 (also pyproject.toml:29-30, infra/Dockerfile:26)
- Problem: `uv pip install --system .` does not read uv.lock; with `[tool.uv] pip = { upgrade = true }` every build re-resolves unpinned transitives (urllib3, kombu, redis, billiard...) to whatever is newest. Dependabot fixes applied to the lock (ec37bac) do not reach the image deterministically; `pip install uv` is also unpinned.
- Proposal: `COPY --from=ghcr.io/astral-sh/uv:<ver> /uv /bin/` then `uv sync --frozen --no-dev --no-install-project` (or `uv export --frozen --no-dev | uv pip install --system -r -`). Drop the `pip.upgrade` setting.
- Effort: S | Risk: venv path changes (PATH / PYTHONPATH in Dockerfile and compose commands).

## 5. Transitive deps pinned as direct dependencies, several vulnerable
- Severity: medium | Category: library | File: pyproject.toml:7,14,18,20,21
- Problem: `asgiref`, `packaging`, `pyjwt`, `sqlparse`, `tzdata` are not imported anywhere (asgiref/sqlparse <- django, packaging <- gunicorn/kombu, pyjwt <- redis, tzdata <- celery/kombu). Exact pins freeze them: `sqlparse==0.5.4` has 5 advisories fixed in 0.6.0, `pyjwt==2.12.0` has advisories fixed in 2.15.x, `tzdata==2025.2` ships stale tz rules. They exist only because of finding 4.
- Proposal: remove them from `dependencies`; once Docker uses the lock (finding 4), uv.lock holds them. If a floor is needed for a CVE, use `[tool.uv] constraint-dependencies = ["pyjwt>=2.15.1"]`.
- Effort: S | Risk: low.

## 6. bleach is deprecated and 6.2.0 has sanitizer bypasses
- Severity: high | Category: security | File: pyproject.toml:8, django/main/views.py:371
- Problem: bleach is marked "Development Status :: 7 - Inactive" upstream. 6.2.0 has GHSA-8rfp-98v4-mmr6 (disallowed URI schemes pass with Unicode > U+00A0) and GHSA-gj48-438w-jh9v, fixed in 6.4.0. `bleach.clean(..., protocols=...)` sanitizes README markdown fetched from GitHub and rendered on project pages.
- Proposal: immediate `bleach==6.4.0`; then replace with `nh3` (0.3.7): `nh3.clean(html, tags=set(...), attributes={...}, url_schemes={...}, attribute_filter=_clean_attributes)`; `_clean_attributes` maps 1:1 (return None instead of False).
- Effort: S (bump) / M (nh3 + tests) | Risk: nh3 attribute_filter signature differs (returns value or None); existing view tests for img src filtering must pass.

## 7. Pillow 12.2.0 has 13 advisories fixed in 12.3.0
- Severity: medium | Category: security | File: pyproject.toml:15
- Problem: heap OOB write in paste/crop, decompression-bomb bypasses, etc. Pillow parses `Project.thumbnail` uploads (django/main/models.py:59); exposure limited to admin uploads.
- Proposal: `pillow==12.3.0`.
- Effort: S | Risk: low.

## 8. Celery 5.4.0 does not support Python 3.13
- Severity: medium | Category: library | File: pyproject.toml:9
- Problem: project requires Python 3.13 (pyproject.toml:5, Dockerfile python:3.13-slim); celery 5.4.0 classifiers stop at 3.12, 3.13 support arrives in 5.5. Latest is 5.6.3.
- Proposal: `celery[redis]==5.6.3`.
- Effort: S | Risk: check beat schedule/retry behaviour in django/main/tasks.py; run task tests.

## 9. Node version drift: CI on EOL Node 20, image on Node 22
- Severity: medium | Category: ci | File: .github/workflows/django.yml:22 (also .github/workflows/docker-build-push.yml:83, infra/Dockerfile:2)
- Problem: CI builds CSS with Node 20 (EOL 2026-04-30); the image uses `node:22-slim`. No `engines` / `.nvmrc` to keep them aligned. Node 24 is active LTS (to 2028-04).
- Proposal: add `.nvmrc` with `24`, use `node-version-file: .nvmrc` in both workflows and `node:24-slim` in Dockerfile.
- Effort: S | Risk: low (Tailwind CLI 4 supports Node 20+).

## 10. Outdated / unpinned GitHub Actions
- Severity: medium | Category: ci | File: .github/workflows/django.yml:18,26 (also docker-build-push.yml:78,81,116,136)
- Problem: `actions/checkout@v3` and `actions/setup-python@v4` target deprecated Node runtimes (latest v7.x); `setup-node@v4` (v7.1.0), `docker/login-action@v3` (v4.6.0), `appleboy/ssh-action@v1.0.3` (v1.2.5). The third-party ssh-action receives `SSH_PRIVATE_KEY` and `GHCR_PAT` but is pinned only by tag. CI also installs uv via unpinned `pip install uv` and runs `uv sync` without `--locked` (django.yml:32-34), so lock drift is not detected.
- Proposal: bump first-party actions to current majors; pin `appleboy/ssh-action` to a commit SHA; use `astral-sh/setup-uv` (v10.3.0) with a pinned version and `uv sync --locked --extra dev`.
- Effort: S | Risk: low.

## 11. MathJax loaded from CDN with floating major and no SRI
- Severity: medium | Category: security | File: django/main/templates/projects/detail.html:52
- Problem: `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` resolves to any 3.x at runtime, without `integrity`/`crossorigin`; a compromised or changed package runs script on every project page. MathJax 4.1.3 is current.
- Proposal: pin exact version (e.g. `mathjax@3.2.2` or migrate to 4.x) with SRI hash, or vendor the file into static/.
- Effort: S | Risk: 4.x config differs from js/mathjax-config.js; staying on pinned 3.2.2 is zero-risk.

## 12. psycopg2-binary instead of psycopg 3; unneeded build packages
- Severity: low | Category: library | File: pyproject.toml:16 (also infra/Dockerfile:17)
- Problem: Django recommends psycopg 3 (psycopg2 support likely to be deprecated); psycopg2 authors advise against `-binary` in production. The Dockerfile installs `gcc libpq-dev` although the binary wheel needs neither (only `postgresql-client` is used by entrypoints/wait-for-db.sh).
- Proposal: `psycopg[binary]==3.3.6` (no settings change, same ENGINE); drop `gcc libpq-dev` from the apt line.
- Effort: S | Risk: low; run DB tests on Postgres.

## 13. Unused npm package @catppuccin/daisyui
- Severity: low | Category: library | File: package.json:13
- Problem: not referenced in input.css (only `@plugin "daisyui"` with built-in themes) or anywhere else.
- Proposal: remove it.
- Effort: S | Risk: none.

## 14. Routine patch/minor bumps available
- Severity: low | Category: library | File: pyproject.toml:11-19,26
- Problem: django-environ 0.12.0 -> 0.14.0, gunicorn 23.0.0 -> 26.2.0 (major), markdown 3.8.2 -> 3.11.1, pymdown-extensions 10.16.1 -> 12.2 (3 CVEs, all in extensions not enabled here; only arithmatex used at views.py:364), requests 2.33.0 -> 2.34.2, ruff 0.11.10 -> 0.17.0. npm: tailwindcss/@tailwindcss/cli ^4.1.4 -> 4.3.3, daisyui ^5.0.28 -> 5.7.50 (caret ranges; lock decides).
- Proposal: bump in one PR after finding 3 makes tests run; gunicorn and pymdown majors with changelog check.
- Effort: S | Risk: gunicorn major default changes; pymdown arithmatex output must still match MathJax config.
