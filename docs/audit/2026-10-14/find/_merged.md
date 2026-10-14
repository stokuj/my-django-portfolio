# Merged audit findings (2026-10-14)

| id | severity | category | file:line | title | lenses |
|----|----------|----------|-----------|-------|--------|
| F-001 | high | ops | .github/workflows/docker-build-push.yml:107 | Deploy has no rollback tag, full downtime, no concurrency guard, not tied to built commit | sec-actions, ops |
| F-002 | high | tests | Makefile:38 | make verify / CI never runs the 96 Django app tests | mattpocock-standards, verify-pipeline, libraries, tests-quality, ponytail-infra |
| F-003 | high | bug | django/main/markdown_sync.py:168 | Markdown sync rewrites the file every run and the filename keeps growing | mattpocock-spec, cr-tasks-integrations, perf-db, tests-quality |
| F-004 | high | bug | django/main/templates/base.html:25 | Mobile menu likely never opens in Safari/iOS; JS reimplements native popover | frontend, ponytail-app |
| F-005 | high | security | django/main/views.py:157 | Public heatmap endpoint fetches GitHub synchronously with no backoff after errors | mattpocock-standards, devkit-core, devkit-integrations, cr-views-models, cr-tasks-integrations, sec-endpoints, arch-modules, perf-db, tests-quality |
| F-006 | high | security | django/main/views.py:371 | bleach 6.2.0 has known sanitizer bypasses and is deprecated upstream | devkit-core, sec-markdown, libraries |
| F-007 | high | ops | infra/docker-compose.prod.yml:3 | PostgreSQL 13 is EOL; upgrade was reverted and blocks Django 5.2 | mattpocock-spec, sec-infra, libraries, ops |
| F-008 | high | ops | infra/docker-compose.prod.yml:33 | web and caddy have no restart policy in prod | sec-infra, ops |
| F-009 | high | ops | infra/docker-compose.prod.yml:46 | Gunicorn runs with defaults: 1 sync worker, 30s timeout, no access log | perf-db, ops |
| F-010 | high | ops | infra/docker-compose.prod.yml:185 | No backups of Postgres or media volume | ops |
| F-011 | high | security | pyproject.toml:10 | Django 5.1 is EOL with unpatched advisories | libraries |
| F-012 | medium | security | .github/workflows/django.yml:9 | No permissions block in CI workflow or deploy job | sec-actions |
| F-013 | medium | ci | .github/workflows/django.yml:18 | CI workflow uses deprecated actions, unlocked uv sync and stale steps | ponytail-infra, verify-pipeline, sec-actions, libraries |
| F-014 | medium | ci | .github/workflows/django.yml:22 | CI builds CSS on EOL Node 20 while the image uses Node 22 | mattpocock-spec, verify-pipeline, libraries, ponytail-infra |
| F-015 | medium | ops | .github/workflows/docker-build-push.yml:80 | workflow_dispatch from any branch overwrites production :latest image | verify-pipeline, sec-actions |
| F-016 | medium | ci | .github/workflows/docker-build-push.yml:84 | Image build/push/deploy not gated on tests | verify-pipeline |
| F-017 | medium | security | .github/workflows/docker-build-push.yml:89 | SSH deploy has no host key verification | sec-actions |
| F-018 | medium | security | .github/workflows/docker-build-push.yml:90 | Third-party ssh-action holding the SSH key is pinned to a mutable, old tag | sec-actions, libraries |
| F-019 | medium | docs | CLAUDE.md:93 | CLAUDE.md describes test commands and CI pipeline that do not exist | mattpocock-standards, ponytail-infra, verify-pipeline, sec-actions |
| F-020 | medium | ci | Makefile:39 | Ruff does not lint the Django app (31 violations) | mattpocock-standards, mattpocock-spec, verify-pipeline |
| F-021 | medium | security | django/config/settings.py:35 | Placeholder SECRET_KEY / DEBUG=True never caught; check --deploy not run | sec-settings |
| F-022 | medium | performance | django/config/settings.py:109 | No persistent DB connections (CONN_MAX_AGE=0) | perf-db |
| F-023 | medium | simplification | django/main/github_client.py:49 | Two HTTP calls and nested isinstance validation where one GraphQL viewer query works | ponytail-app |
| F-024 | medium | ops | django/main/middleware.py:15 | Cookieless home hits create session rows that are never purged | devkit-integrations, sec-endpoints, perf-db |
| F-025 | medium | bug | django/main/models.py:47 | Admin 500 when adding a tag that differs only in case | devkit-core, cr-views-models |
| F-026 | medium | bug | django/main/models.py:238 | Media file deleted even when the DB transaction rolls back | devkit-core, cr-views-models |
| F-027 | medium | security | django/main/static/js/mathjax-config.js:1 | MathJax typesets sanitized text without ui/safe (\href{javascript:}) | sec-markdown |
| F-028 | medium | frontend | django/main/static/js/theme-toggle.js:32 | Dark mode ignores OS preference, flashes light, carries legacy migration code | ponytail-app, frontend |
| F-029 | medium | bug | django/main/static/src/css/input.css:9 | Unlayered h1/h2/h3 rules override all Tailwind font sizes | frontend |
| F-030 | medium | simplification | django/main/tasks.py:119 | Task status bookkeeping copy-pasted ~5x plus a redundant no-token branch | mattpocock-standards, ponytail-app, devkit-core, cr-tasks-integrations, arch-modules |
| F-031 | medium | tests | django/main/tasks.py:145 | Task failure branches and blog_slug filter not covered | tests-quality |
| F-032 | medium | ops | django/main/tasks.py:202 | Disk monitoring runs once a day and alerts nobody | ops |
| F-033 | medium | simplification | django/main/tasks.py:250 | Dead self-rescheduling path (schedule_next, _schedule_next_heatmap_refresh) | mattpocock-standards, ponytail-app, devkit-core, cr-views-models, cr-tasks-integrations, sec-endpoints, arch-modules, perf-db, tests-quality, ops |
| F-034 | medium | bug | django/main/templates/pages/about.html:3 | Every page is titled 'My Portfolio' (wrong block name) | frontend |
| F-035 | medium | security | django/main/templates/projects/detail.html:52 | MathJax from CDN with floating version, no SRI, and no CSP anywhere | sec-markdown, sec-infra, libraries, frontend |
| F-036 | medium | frontend | django/main/templates/projects/index.html:40 | Server-rendered project grid hidden behind a fake skeleton until JS runs | ponytail-app, frontend |
| F-037 | medium | tests | django/main/tests/test_markdown_sync.py:15 | Markdown download guards untested; mock skips the Content-Length path | tests-quality |
| F-038 | medium | tests | django/main/tests/test_views.py:77 | 'Heatmap disabled' tests always pass and depend on local .env | tests-quality |
| F-039 | medium | tests | django/main/tests/test_views.py:632 | Disk threshold fix (d2b6257) has no regression test; view test reads real disk | tests-quality |
| F-040 | medium | bug | django/main/views.py:95 | Custom 500 handler hits the DB and re-implements Django defaults | ponytail-app, cr-views-models, arch-modules |
| F-041 | medium | architecture | django/main/views.py:264 | Admin jobs panel hard-codes beat schedule, wrong next-run time, omits disk task | mattpocock-standards, ponytail-app, devkit-core, cr-views-models, arch-modules |
| F-042 | medium | tests | django/main/views.py:357 | No negative tests for the markdown sanitizer (XSS boundary) | sec-markdown, tests-quality |
| F-043 | medium | docs | docs/superpowers/plans/2026-05-14-codebase-audit.md:1 | Obsolete/divergent specs and plans in docs/superpowers | mattpocock-spec, ponytail-infra |
| F-044 | medium | security | infra/Caddyfile:18 | Caddy-served /static and /media get no security headers | sec-settings, sec-infra |
| F-045 | medium | library | infra/Dockerfile:27 | Docker image ignores uv.lock; transitive deps float per build | ponytail-infra, verify-pipeline, sec-infra, libraries |
| F-046 | medium | security | infra/Dockerfile:33 | Runtime user owns the application code | sec-infra |
| F-047 | medium | simplification | infra/docker-compose.prod.yml:52 | App service and logging blocks repeated 6x across compose files | ponytail-infra, sec-infra |
| F-048 | medium | ops | infra/docker-compose.prod.yml:87 | No healthchecks; startup ordering by sleep and an endless wait-for-db loop | ponytail-infra, sec-infra, ops |
| F-049 | medium | simplification | infra/scripts/compose_status.py:1 | Python helpers re-implement docker ps --format and copy-if-missing | mattpocock-spec, ponytail-infra |
| F-050 | medium | library | pyproject.toml:7 | Transitive packages pinned as direct deps, some vulnerable | ponytail-infra, libraries |
| F-051 | medium | library | pyproject.toml:9 | Celery 5.4.0 does not support Python 3.13 | libraries |
| F-052 | medium | security | pyproject.toml:15 | Pillow 12.2.0 has advisories fixed in 12.3.0 | libraries |
| F-053 | medium | tests | tests/test_operational_files.py:51 | String-grep change-detector tests on Makefile/compose/workflow | ponytail-infra |
| F-054 | low | ci | .github/dependabot.yml:1 | No Dependabot config for GitHub Actions | sec-actions |
| F-055 | low | ci | .github/workflows/docker-build-push.yml:16 | Build workflow duplication: job env, dead IMAGE_NAME, preflight CSS, master fallbacks | ponytail-infra, verify-pipeline |
| F-056 | low | security | .github/workflows/docker-build-push.yml:103 | Long-lived GHCR PAT pasted into the remote script | sec-actions |
| F-057 | low | simplification | .gitignore:34 | .gitignore is the full GitHub Python template | ponytail-infra |
| F-058 | low | simplification | Makefile:35 | compileall in verify is redundant | ponytail-infra |
| F-059 | low | bug | django/config/settings.py:43 | ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS entries are not stripped | sec-settings |
| F-060 | low | security | django/config/settings.py:102 | HSTS includeSubDomains + preload hardcoded for one year | sec-settings |
| F-061 | low | simplification | django/config/settings.py:181 | Dead/default settings: STATICFILES_STORAGE, Env(DEBUG), result backend, Polish comments | mattpocock-standards, mattpocock-spec, ponytail-app, cr-tasks-integrations, sec-settings |
| F-062 | low | ops | django/config/settings.py:214 | No Celery task time limit | ops |
| F-063 | low | docs | django/config/settings.py:220 | Beat entry 'sync-project-markdowns-hourly' runs every 2h | cr-tasks-integrations, ops, mattpocock-standards, ponytail-app |
| F-064 | low | performance | django/main/context_processors.py:10 | Three uncached queries per template render | perf-db |
| F-065 | low | simplification | django/main/context_processors.py:28 | Active-profile lookup repeated 3x; processor flattens model into 15 keys | ponytail-app |
| F-066 | low | tests | django/main/github_client.py:57 | GitHub client and heatmap error mapping partly untested | tests-quality |
| F-067 | low | bug | django/main/github_client.py:60 | GitHub rate-limit 403 reported as 'token invalid or expired' | devkit-integrations |
| F-068 | low | simplification | django/main/heatmap.py:68 | Unused override params, re-defaulted settings, redundant login re-validation | ponytail-app, devkit-integrations, arch-modules |
| F-069 | low | architecture | django/main/markdown_sync.py:13 | Hard-coded BLOG_REPO_PATHS duplicates Project.github_url | ponytail-app |
| F-070 | low | simplification | django/main/markdown_sync.py:105 | Redundant exception handling around requests, duplicate size check, hand-rolled dedup | ponytail-app, devkit-integrations, cr-tasks-integrations |
| F-071 | low | performance | django/main/middleware.py:10 | Redundant queries in visitor middleware and snapshot updates | perf-db |
| F-072 | low | architecture | django/main/models.py:118 | TaskExecutionStatus duplicates the latest TaskExecutionLog row | ponytail-app |
| F-073 | low | bug | django/main/static/js/mathjax-config.js:3 | $...$ delimiters typeset dollar amounts anywhere on the page | sec-markdown, frontend |
| F-074 | low | frontend | django/main/static/js/projects-filters.js:16 | Unnecessary debounce and JS clear button in projects filter | ponytail-app |
| F-075 | low | frontend | django/main/static/js/projects-filters.js:76 | Tag filter state shown only by color (no aria-pressed) | frontend |
| F-076 | low | bug | django/main/tasks.py:36 | Single-slug or empty runs overwrite global markdown status as SUCCESS | cr-tasks-integrations |
| F-077 | low | bug | django/main/tasks.py:74 | last_success_at is cleared on every failure | cr-tasks-integrations |
| F-078 | low | ops | django/main/tasks.py:260 | TaskExecutionLog grows without bound, no index on ordering column | cr-tasks-integrations, perf-db, ops |
| F-079 | low | bug | django/main/templates/base.html:54 | Navbar breakpoints mismatch (both menus visible at md) | frontend |
| F-080 | low | frontend | django/main/templates/base.html:152 | Nav and footer semantics (aria-current, role=status, duplicate links) | frontend |
| F-081 | low | simplification | django/main/templates/base.html:165 | Dead CSS classes (hover:bg-primary-focus, menu-compact, prose) | frontend |
| F-082 | low | performance | django/main/templates/components/hero_section.html:2 | Heavy hero PNGs under an overlay; one image unused | frontend |
| F-083 | low | frontend | django/main/templates/components/timeline_section.html:2 | Timeline accordion uses unlabelled radio inputs | frontend |
| F-084 | low | simplification | django/main/templates/pages/about.html:260 | Heatmap inline JS over-generalised (one-element variants, dead tooltip mode) | ponytail-app, frontend |
| F-085 | low | frontend | django/main/templates/pages/about.html:421 | Heatmap is not accessible | frontend |
| F-086 | low | simplification | django/main/templates/projects/components/project_card.html:9 | Template duplication (img blocks, status badge, social icons) | frontend |
| F-087 | low | tests | django/main/tests/test_models.py:289 | Audit spec 1b/2a paths without tests (markdown_file cleanup, camo/github images) | mattpocock-spec |
| F-088 | low | tests | django/main/tests/test_views.py:58 | Redundant legacy assertions and weak status checks | tests-quality |
| F-089 | low | bug | django/main/urls.py:5 | Duplicate URL name 'home'; reverse resolves to /home/ | cr-views-models, ponytail-app |
| F-090 | low | security | django/main/views.py:64 | Unrestricted class on div/span allows page-overlay UI redressing | sec-markdown |
| F-091 | low | simplification | django/main/views.py:103 | Home timeline duplicates Project.STATUS_CHOICES | ponytail-app |
| F-092 | low | simplification | django/main/views.py:200 | _calculate_last_30_days_total defensively re-parses our own payload | ponytail-app, arch-modules |
| F-093 | low | simplification | django/main/views.py:240 | Disk check implemented twice (view and task) | arch-modules, mattpocock-standards, ponytail-app |
| F-094 | low | simplification | django/main/views.py:340 | Small dead bits in views and templates | ponytail-app |
| F-095 | low | security | django/main/views.py:371 | Outbound README links get no rel=nofollow/noopener | sec-markdown |
| F-096 | low | performance | django/main/views.py:402 | Blog markdown re-read and re-rendered on every request | perf-db |
| F-097 | low | tests | django/main/views.py:422 | Staff endpoints: authorization and error branches thinly tested | tests-quality |
| F-098 | low | docs | docs/implementation.md:36 | Task docs out of sync (healthcheck_task unused, disk task undocumented) | mattpocock-standards |
| F-099 | low | performance | infra/Caddyfile:16 | Static assets served uncompressed and without cache headers | frontend |
| F-100 | low | simplification | infra/Caddyfile:18 | Duplicate static/media file_server blocks | ponytail-infra |
| F-101 | low | security | infra/Dockerfile:2 | Floating base image tags; app deployed only as :latest | sec-infra |
| F-102 | low | security | infra/Dockerfile:16 | Build toolchain (gcc, libpq-dev) shipped in runtime image | sec-infra, ponytail-infra, libraries |
| F-103 | low | security | infra/docker-compose.prod.yml:10 | Prod Postgres published on host loopback | ponytail-infra, sec-infra |
| F-104 | low | security | infra/docker-compose.prod.yml:180 | Single explicit bridge network: redundant and flat | ponytail-infra, sec-infra |
| F-105 | low | library | package.json:13 | Unused @catppuccin/daisyui devDependency | ponytail-infra, libraries, frontend |
| F-106 | low | library | pyproject.toml:11 | Routine patch/minor bumps available | libraries |
| F-107 | low | library | pyproject.toml:16 | psycopg2-binary instead of psycopg 3 | libraries |
